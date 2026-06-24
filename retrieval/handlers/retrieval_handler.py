import csv
import json

from rank_bm25 import BM25Okapi
from openai import OpenAI
import numpy as np


def tokenize(sentence: str):
    return sentence.lower().split()


def load_chunks(csv_file: str):
    chunks = []

    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            chunks.append({
                "url": row["url"],
                "chunk_id": row["chunk_id"],
                "chunk_text": row["chunk_text"],
                "chunk_embedding": json.loads(row["embedding"])
            })

    return chunks


def build_bm25_index(chunks):
    tokenized_corpus = [
        tokenize(chunk["chunk_text"]) for chunk in chunks
    ]
    bm25 = BM25Okapi(tokenized_corpus)

    return bm25


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)

    return np.dot(a, b) / (
        np.linalg.norm(a) * np.linalg.norm(b)
    )


def search(
    query: str,
    bm25: BM25Okapi,
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

    # TODO: Use sklearn for faster calcuation
    semantic_scores = [
        cosine_similarity(
            query_embedding,
            chunk["chunk_embedding"],
        )
        for chunk in chunks
    ]

    semantic_ranked = sorted(
        zip(chunks, semantic_scores),
        key=lambda x: x[1],
        reverse=True,
    )

    semantic_candidates = semantic_ranked[:top_k]

    # Merge + deduplicate
    candidate_dict = {}

    for chunk, score in lexical_candidates:
        key = (
            chunk["url"],
            chunk["chunk_id"],
        )

        candidate_dict[key] = {
            "url": chunk["url"],
            "chunk_id": chunk["chunk_id"],
            "chunk_text": chunk["chunk_text"],
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
                "url": chunk["url"],
                "chunk_id": chunk["chunk_id"],
                "chunk_text": chunk["chunk_text"],
                "lexical_score": None,
                "semantic_score": float(score),
            }

    candidate_results = list(
        candidate_dict.values()
    )

    return candidate_results