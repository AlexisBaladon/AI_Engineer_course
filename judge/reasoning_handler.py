import json

from openai import OpenAI


JUDGE_MODEL = "gpt-4.1-mini"


def _build_context(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"Document {i+1}:\n{chunk['chunk_text']}"
        for i, chunk in enumerate(chunks)
    )


def judge_context(
    query: str,
    chunks: list[dict],
    openai_client: OpenAI,
    model: str = JUDGE_MODEL,
):
    context = _build_context(chunks)

    response = openai_client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are evaluating whether the retrieved context "
                    "contains enough information to answer ALL the user's "
                    "question.\n\n"
                    "Answer ONLY with JSON using this schema:\n"
                    "{\n"
                    '  "enough_context": true,\n'
                    "}"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question:\n{query}\n\n"
                    f"Retrieved documents:\n{context}"
                ),
            },
        ],
    )

    return json.loads(
        response.choices[0].message.content
    )


def rewrite_query(
    query: str,
    chunks: list[dict],
    openai_client: OpenAI,
    model: str = JUDGE_MODEL,
):
    context = _build_context(chunks)

    response = openai_client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "You rewrite search queries to maximize retrieval "
                    "quality, speially around missing information in the context.\n\n"
                    "The rewritten query should:\n"
                    "- preserve the original intent;\n"
                    "- include important keywords;\n"
                    "- avoid ambiguity;\n"
                    "- be concise;\n"
                    "- NEVER answer the question.\n\n"
                    "Return ONLY the rewritten query."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Original question:\n{query}\n\n"
                    f"Retrieved documents:\n{context}"
                ),
            },
        ],
    )

    return response.choices[0].message.content.strip()