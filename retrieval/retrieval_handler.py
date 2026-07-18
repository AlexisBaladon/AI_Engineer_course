import csv
import json
from collections import defaultdict

from rank_bm25 import BM25Okapi
from openai import OpenAI
import numpy as np
import faiss


def tokenize(sentence: str):
    return sentence.lower().split()


def load_chunks(csv_file: str, images_file: str):
    """
    Loads chunk metadata and associates every chunk with the
    images found on the page it belongs to.
    """

    images_by_url = defaultdict(list)

    with open(images_file, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            images_by_url[row["page_url"]].append(row["image_url"])

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
        tokenize(chunk["chunk_text"]) for chunk in chunks
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


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)

    return np.dot(a, b) / (
        np.linalg.norm(a) * np.linalg.norm(b)
    )


def search(
    query: str,
    bm25: BM25Okapi,
    faiss_index: faiss.IndexFlatIP,
    openai_client: OpenAI,
    chunks: list[dict],
    top_k: int = 10,
    embedding_model: str = "text-embedding-3-small",
):
    # Lexical retrieval
    tokenized_query = tokenize(query)

    bm25_scores = bm25.get_scores(
        tokenized_query
    )

    lexical_ranked = sorted(
        zip(chunks, bm25_scores),
        key=lambda x: x[1],
        reverse=True,
    )

    lexical_candidates = lexical_ranked[:top_k]

    # Semantic retrieval
    query_embedding = (
        openai_client.embeddings.create(
            model=embedding_model,
            input=query,
        )
        .data[0]
        .embedding
    )

    query_embedding = np.array(
        [query_embedding],
        dtype=np.float32,
    )

    faiss.normalize_L2(query_embedding)

    scores, indices = faiss_index.search(
        query_embedding,
        top_k,
    )

    semantic_candidates = []

    for score, index in zip(scores[0], indices[0]):
        if index == -1:
            continue

        semantic_candidates.append(
            (
                chunks[index],
                float(score),
            )
        )

    semantic_candidates = semantic_candidates[:top_k]

    # Merge + deduplicate
    candidate_dict = {}

    for chunk, score in lexical_candidates:
        key = (
            chunk["url"],
            chunk["chunk_id"],
        )

        candidate_dict[key] = {
            **chunk,
            "lexical_score": float(score),
            "semantic_score": None,
        }

    for chunk, score in semantic_candidates:
        key = (
            chunk["url"],
            chunk["chunk_id"],
        )

        if key in candidate_dict:
            candidate_dict[key]["semantic_score"] = float(score)
        else:
            candidate_dict[key] = {
                **chunk,
                "lexical_score": None,
                "semantic_score": float(score),
            }

    candidate_results = list(
        candidate_dict.values()
    )

    return candidate_results