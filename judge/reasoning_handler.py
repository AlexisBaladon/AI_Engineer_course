from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI
from langsmith import traceable

import json


LLM_CACHE = {}


def _cache_key(messages: list, llm: ChatOpenAI) -> str:
    return json.dumps(
        {
            "model": llm.model_name,
            "messages": [m.model_dump() for m in messages],
        },
        sort_keys=True,
        default=str,
    )


def _build_context(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"Document {i + 1}:\n{chunk['chunk_text']}"
        for i, chunk in enumerate(chunks)
    )

@traceable(type="llm", name="Judge context")
def judge_context(
    query: str,
    chunks: list[dict],
    llm: ChatOpenAI,
    user_id="default",
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

    key = _cache_key(messages, llm)

    cached = LLM_CACHE.get(key)
    if cached is not None:
        return cached

    response = llm.bind(user=user_id).invoke(messages)

    result = json.loads(response.content)

    LLM_CACHE[key] = result

    return result


@traceable(type="llm", name="Rewrite query")
def rewrite_query(
    query: str,
    chunks: list[dict],
    llm: ChatOpenAI,
    user_id="default",
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

    key = _cache_key(messages, llm)

    cached = LLM_CACHE.get(key)
    if cached is not None:
        return cached

    response = llm.bind(user=user_id).invoke(messages)

    result = response.content

    LLM_CACHE[key] = result

    return result