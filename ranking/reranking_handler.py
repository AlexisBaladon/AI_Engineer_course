from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langsmith import traceable

import json


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

@traceable(type="llm", name="Rerank documents")
def rerank_chunks(
    query: str,
    chunks: list[dict],
    user_id: str,
    llm: ChatOpenAI,
    reranking_prompt=RERANKING_PROMPT,
):
    docs = []

    for i, chunk in enumerate(chunks):
        docs.append(f"[{i}]\n{chunk['chunk_text']}")

    prompt = reranking_prompt.format(query=query, documents="\n".join(docs))
    response = llm.bind(user=user_id).invoke(
        [
            HumanMessage(content=prompt)
        ]
    )
    ranking = json.loads(response.content)

    return [chunks[i] for i in ranking]