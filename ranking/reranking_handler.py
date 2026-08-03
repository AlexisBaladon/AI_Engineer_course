from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langsmith import traceable

import json


RERANK_CACHE = {}

RERANKING_PROMPT = """
Query:
{query}

Documents:
{documents}

Rank all documents from most relevant to least relevant.

Return ONLY a JSON array of indices.

Example:
[3, 1, 0, 2]
"""


def _safe_parse_ranking(content: str, n_documents: int) -> list[int]:
    """
    Parses and sanitizes the ranking returned by the LLM.

    Guarantees:
    - Only integers are kept.
    - Out-of-range indices are discarded.
    - Duplicates are removed.
    - Missing indices are appended at the end.
    """

    try:
        ranking = json.loads(content)
    except json.JSONDecodeError:
        return list(range(n_documents))

    if not isinstance(ranking, list):
        return list(range(n_documents))

    cleaned = []
    seen = set()

    for item in ranking:
        try:
            idx = int(item)
        except (TypeError, ValueError):
            continue

        if 0 <= idx < n_documents and idx not in seen:
            cleaned.append(idx)
            seen.add(idx)

    # Append missing documents preserving their original order
    for idx in range(n_documents):
        if idx not in seen:
            cleaned.append(idx)

    return cleaned


@traceable(run_type="llm", name="Rerank documents")
def rerank_chunks(
    query: str,
    chunks: list[dict],
    user_id: str,
    llm: ChatOpenAI,
    reranking_prompt=RERANKING_PROMPT,
):
    if not chunks:
        return []

    docs = [
        f"[{i}]\n{chunk['chunk_text']}"
        for i, chunk in enumerate(chunks)
    ]

    prompt = reranking_prompt.format(
    query=query,
    documents="\n".join(docs),
)

    cache_key = prompt

    ranking = RERANK_CACHE.get(cache_key)

    if ranking is None:
        try:
            response = llm.bind(user=user_id).invoke(
                [HumanMessage(content=prompt)]
            )

            ranking = _safe_parse_ranking(
                response.content,
                len(chunks),
            )

        except Exception:
            ranking = list(range(len(chunks)))

        RERANK_CACHE[cache_key] = ranking

    return [chunks[i] for i in ranking]