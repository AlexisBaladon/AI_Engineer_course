import csv
from rank_bm25 import BM25Okapi


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
            })

    return chunks


def build_bm25_index(chunks):
    tokenized_corpus = [
        tokenize(chunk["chunk_text"]) for chunk in chunks
    ]
    bm25 = BM25Okapi(tokenized_corpus)

    return bm25


def search(
    query: str,
    bm25: BM25Okapi,
    chunks,
    top_k: int = 5,
):
    tokenized_query = tokenize(query)
    scores = bm25.get_scores(tokenized_query)

    # Scores are not sorted by default
    ranked = sorted(
        zip(chunks, scores),
        key=lambda x: x[1],
        reverse=True,
    )

    top_results = ranked[:top_k]

    # Add "score" as a field
    top_results = [
        {
            "url": chunk["url"],
            "chunk_id": chunk["chunk_id"],
            "score": float(score),
            "chunk_text": chunk["chunk_text"],
        }
        for chunk, score in top_results
    ]

    return top_results

