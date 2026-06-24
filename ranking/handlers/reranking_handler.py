import json

from openai import OpenAI


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


def rerank_chunks(
    query: str,
    chunks: list[dict],
    openai_client: OpenAI,
    model: str = "gpt-4.1-mini",
    reranking_prompt=RERANKING_PROMPT,
):
    docs = []

    for i, chunk in enumerate(chunks):
        docs.append(f"[{i}]\n{chunk['chunk_text']}")

    prompt = reranking_prompt.format(query=query, documents=chr(10).join(docs))
    response = openai_client.responses.create(model=model, input=prompt)
    ranking = json.loads(response.output_text)

    return [chunks[i] for i in ranking]