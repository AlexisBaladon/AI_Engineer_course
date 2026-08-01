import csv
import json
from collections import defaultdict
import re

from rank_bm25 import BM25Okapi
from langchain_openai import OpenAIEmbeddings
import numpy as np
import faiss
from langsmith import traceable


SPANISH_STOPWORDS = {
    "a", "acá", "ahí", "al", "algo", "algún", "alguna", "algunas", "alguno", "algunos", "allá", "allí", "ambos", "ante", "antes", "aquel", "aquella", "aquellas", "aquello", "aquellos", "aquí", "arriba", "así", "atrás", "aun", "aunque",     "bajo", "bastante", "bien", "cada", "casi", "como", "con", "contra", "cual", "cuales", "cualquier", "cualquiera", "cuando", "cuanto", "cuánto", "cuanta", "cuántas", "cuantos", "cuántos","de", "debajo", "del", "desde", "demás", "demasiado", "dentro", "después", "donde", "dos", "durante","e", "el", "él", "ella", "ellas", "ello", "ellos", "en", "encima", "entre", "era", "eran", "eres", "es", "esa", "esas", "ese", "eso", "esos", "esta", "está", "estaba", "estaban", "estado", "estáis", "estamos", "están", "estar", "estas", "este", "esto", "estos", "estoy","fue", "fueron", "fui", "fuimos","ha", "había", "habían", "haber", "habrá", "habrán", "hace", "hacen", "hacer", "hacia", "han", "hasta", "hay", "he", "hemos", "hubo","incluso","jamás","la", "las", "le", "les", "lo", "los", "más", "me", "menos", "mi", "mis", "mientras", "mío", "mía", "míos", "mías", "muy","nada", "nadie", "ni", "ningún", "ninguna", "ninguno", "ningunos", "no", "nos", "nosotras", "nosotros", "nuestra", "nuestras", "nuestro", "nuestros", "nunca","o", "os", "otra", "otras", "otro", "otros","para", "pero", "poco", "por", "porque", "primero", "puede", "pueden", "puedo", "pues","que", "qué", "quien", "quién", "quienes", "quiénes","se", "sea", "sean", "según", "ser", "si", "sí", "siempre", "siendo", "sin", "sobre", "sois", "solamente", "solo", "somos", "soy", "su", "sus","tal", "también", "tampoco", "tan", "te", "tenemos", "tener", "tengo", "ti", "tiene", "tienen", "toda", "todas", "todavía", "todo", "todos", "tras", "tú", "tu", "tus","un", "una", "unas", "uno", "unos", "usted", "ustedes","va", "vamos", "van", "varias", "varios", "veces","y", "ya","yo"
}


def tokenize_and_clean(text: str) -> list[str]:
    # Split camelCase / PascalCase
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)

    text = text.lower()

    # Split snake_case, kebab-case, dotted names, etc.
    text = re.sub(r"[._/\-]", " ", text)

    # Extract alphanumeric tokens
    tokens = re.findall(r"[a-z0-9]+", text)

    return [
        token
        for token in tokens
        if token not in SPANISH_STOPWORDS
    ]


def load_chunks(csv_file: str, images_file: str):
    """
    Loads chunk metadata and associates every chunk with the
    images found on the page it belongs to.
    """

    images_by_url = defaultdict(list)

    with open(images_file, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            image_alt = row.get("alt", None)
            image_alt = image_alt if image_alt else None

            images_by_url[row["page_url"]].append(
                {
                    "image_url": row["image_url"],
                    "description": image_alt,
                }
            ) 

    chunks = []

    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            url = row["url"]

            chunks.append({
                "url": url,
                "chunk_id": row["chunk_id"],
                "chunk_text": row["chunk_text"],
                "chunk_embedding": json.loads(row["embedding"]),
                "images": images_by_url.get(url, []),
            })

    return chunks


def build_bm25_index(chunks):
    tokenized_corpus = [
        tokenize_and_clean(chunk["chunk_text"]) for chunk in chunks
    ]
    bm25 = BM25Okapi(tokenized_corpus)

    return bm25


def build_faiss_index(chunks):
    embeddings = np.array(
        [chunk["chunk_embedding"] for chunk in chunks],
        dtype=np.float32,
    )

    # Normalize so inner product == cosine similarity
    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    return index


@traceable(run_type="llm", name="Hybrid search")
def search(
    query: str,
    bm25: BM25Okapi,
    faiss_index: faiss.IndexFlatIP,
    embeddings: OpenAIEmbeddings,
    chunks: list[dict],
    top_k: int = 10,
    semantic_weight: float = 0.75,
    user_id=None,
):
    # ---------- Lexical retrieval ----------
    tokenized_query = tokenize_and_clean(query)

    bm25_scores = np.asarray(
        bm25.get_scores(tokenized_query),
        dtype=np.float32,
    )

    # ---------- Semantic retrieval ----------
    query_embedding = embeddings.embed_query(
        query,
        user=user_id,
    )

    query_embedding = np.asarray(
        [query_embedding],
        dtype=np.float32,
    )

    faiss.normalize_L2(query_embedding)

    semantic_scores, semantic_indices = faiss_index.search(
        query_embedding,
        min(len(chunks), top_k * 5),
    )

    # ---------- Normalize BM25 ----------
    bm25_min = bm25_scores.min()
    bm25_max = bm25_scores.max()

    if bm25_max > bm25_min:
        bm25_scores = (
            bm25_scores - bm25_min
        ) / (
            bm25_max - bm25_min
        )
    else:
        bm25_scores = np.zeros_like(bm25_scores)

    # ---------- Normalize semantic scores ----------
    semantic_score_dict = {}

    if len(semantic_scores[0]) > 0:
        scores = np.asarray(
            semantic_scores[0],
            dtype=np.float32,
        )

        s_min = scores.min()
        s_max = scores.max()

        if s_max > s_min:
            scores = (scores - s_min) / (s_max - s_min)
        else:
            scores = np.ones_like(scores)

        for score, index in zip(scores, semantic_indices[0]):
            if index != -1:
                semantic_score_dict[index] = float(score)

    # ---------- Weighted hybrid score ----------
    hybrid_results = []

    lexical_weight = 1.0 - semantic_weight

    for idx, chunk in enumerate(chunks):

        lexical_score = float(bm25_scores[idx])
        semantic_score = semantic_score_dict.get(idx, 0.0)

        hybrid_score = (
            lexical_weight * lexical_score
            + semantic_weight * semantic_score
        )

        hybrid_results.append(
            {
                **chunk,
                "lexical_score": lexical_score,
                "semantic_score": semantic_score,
                "hybrid_score": hybrid_score,
            }
        )

    hybrid_results.sort(
        key=lambda x: x["hybrid_score"],
        reverse=True,
    )



    return hybrid_results[:top_k]