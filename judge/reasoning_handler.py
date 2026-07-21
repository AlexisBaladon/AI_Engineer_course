from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI

import json


def _build_context(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"Document {i + 1}:\n{chunk['chunk_text']}"
        for i, chunk in enumerate(chunks)
    )


def judge_context(
    query: str,
    chunks: list[dict],
    llm: ChatOpenAI,
):
    context = _build_context(chunks)
    messages = [
        SystemMessage(
            content=(
                "You are evaluating whether the retrieved context "
                "contains enough information to answer ALL the user's "
                "question."
                "Answer ONLY with JSON using this schema:\n"
                "{\n"
                '  "enough_context": true,\n'
                "}"
            )
        ),
        HumanMessage(
            content=(
                f"Question:\n{query}\n\n"
                f"Retrieved documents:\n{context}"
            )
        ),
    ]
    response = llm.invoke(messages)

    return json.loads(response.content)


def rewrite_query(
    query: str,
    chunks: list[dict],
    llm: ChatOpenAI,
):
    context = _build_context(chunks)
    messages = [
        SystemMessage(
            content=(
                "You rewrite search queries to maximize retrieval "
                "quality, especially around missing information in the "
                "retrieved context.\n\n"
                "The rewritten query should:\n"
                "- preserve the original intent;\n"
                "- include important keywords;\n"
                "- avoid ambiguity;\n"
                "- be concise;\n"
                "- NEVER answer the question.\n\n"
                "Return ONLY the rewritten query."
            )
        ),
        HumanMessage(
            content=(
                f"Original question:\n{query}\n\n"
                f"Retrieved documents:\n{context}"
            )
        ),
    ]
    response = llm.invoke(messages)

    return response.content