import csv
import json

from rank_bm25 import BM25Okapi
from openai import OpenAI
import numpy as np


client = OpenAI()


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


def min_max_normalize(values):
    min_v = min(values)
    max_v = max(values)

    if max_v == min_v:
        return [1.0] * len(values)

    return [
        (v - min_v) / (max_v - min_v)
        for v in values
    ]


def search(
    query: str,
    bm25: BM25Okapi,
    chunks,
    top_k: int = 5,
    lexical_weight: float = 0.5,
    semantic_weight: float = 0.5,
    embedding_model: str = "text-embedding-3-small",
    client=client,
):

    # Keyword search
    tokenized_query = tokenize(query)
    bm25_scores = bm25.get_scores(
        tokenized_query
    )

    # Semantic search
    query_embedding = client.embeddings.create(
        model=embedding_model,
        input=query,
    ).data[0].embedding

    semantic_scores = [
        cosine_similarity(
            query_embedding,
            chunk["chunk_embedding"],
        )
        for chunk in chunks
    ]

    # Normalize both score distributions
    bm25_scores_norm = min_max_normalize(
        bm25_scores
    )

    semantic_scores_norm = (
        min_max_normalize(
            semantic_scores
        )
    )

    # Hybrid score
    hybrid_scores = [
        lexical_weight * bm25_score + semantic_weight * semantic_score
        for bm25_score, semantic_score in zip(
            bm25_scores_norm,
            semantic_scores_norm,
        )
    ]

    ranked = sorted(
        zip(
            chunks,
            hybrid_scores,
            bm25_scores,
            semantic_scores,
        ),
        key=lambda x: x[1],
        reverse=True,
    )

    top_results = ranked[:top_k]
    top_results_casted = []

    for chunk, hybrid_score, bm25_score, semantic_score, in top_results:
        new_result_datapoint = {
            "url": chunk["url"],
            "chunk_id": chunk["chunk_id"],
            "hybrid_score": float(hybrid_score),
            "lexical_score": float(bm25_score),
            "semantic_score": float(semantic_score),
            "chunk_text": chunk["chunk_text"],
        }
        top_results_casted.append(new_result_datapoint)

    return top_results_casted