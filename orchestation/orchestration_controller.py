import requests

from prompts_handler import (
    fill_user_prompt,
    system_prompt,
)
from constants import (
    RETRIEVAL_HOST,
    RETRIEVAL_PORT,
    RANKING_HOST,
    RANKING_PORT,
    JUDGE_HOST,
    JUDGE_PORT,
    REWRITE_HOST,
    REWRITE_PORT,
    GENERATION_HOST,
    GENERATION_PORT,
    HOOK_HOST,
    HOOK_PORT,
)
from graph_handler import (
    RAGState,
)


def _get_last_message(user_conversation: list[dict]):
    return next(
        (
            message["content"]
            for message in reversed(user_conversation)
            if message["role"] == "user"
        ),
        None,
    )


def retrieve_node(state: RAGState):
    query = state.get("query")

    if query is None:
        query = _get_last_message(state["user_conversation"])

    retrieval_response = requests.get(
        f"http://{RETRIEVAL_HOST}:{RETRIEVAL_PORT}/retrieve",
        params={"query": query, "top_k": 5},
        timeout=30,
    )

    retrieval_response.raise_for_status()

    retrieved_chunks = retrieval_response.json()

    return {
        "query": query,
        "retrieved_chunks": retrieved_chunks,
    }


def rank_node(state: RAGState):
    payload = {
        "query": state["query"],
        "chunks": state["retrieved_chunks"],
        "top_k": 3,
    }

    ranked_response = requests.post(
        f"http://{RANKING_HOST}:{RANKING_PORT}/rank",
        json=payload,
        timeout=30,
    )

    ranked_response.raise_for_status()

    ranked_chunks = ranked_response.json()

    return {
        "retrieved_chunks": ranked_chunks,
    }


def judge_context_node(state: RAGState):

    payload = {
        "query": state["query"],
        "chunks": state["retrieved_chunks"],
    }

    response = requests.post(
        f"http://{JUDGE_HOST}:{JUDGE_PORT}/judge",
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    result = response.json()

    return {
        "enough_context": result["enough_context"],
    }


def rewrite_query_node(state: RAGState):

    payload = {
        "query": state["query"],
        "chunks": state["retrieved_chunks"],
    }

    response = requests.post(
        f"http://{REWRITE_HOST}:{REWRITE_PORT}/rewrite",
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    result = response.json()

    rewritten_query = result["query"]

    return {
        "query": rewritten_query,
        "iteration": state["iteration"] + 1,
        "query_history": (
            state["query_history"]
            + [rewritten_query]
        ),
    }


def build_prompt_node(state: RAGState):
    role = state["role"]
    chunks = state["retrieved_chunks"]
    documents =  [chunk["chunk_text"] for chunk in chunks]
    images = [chunk["images"] for chunk in chunks]
    urls = [chunk["url"] for chunk in chunks]
    rag_prompt = fill_user_prompt(state["query"], documents, urls, images, role)
    
    conversation_for_generation = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]
    conversation_for_generation.extend(state["user_conversation"][:-1])
    conversation_for_generation.append(
        {
            "role": "user",
            "content": rag_prompt,
        }
    )

    return {"conversation_for_generation": conversation_for_generation}


def generate_node(state: RAGState):
    payload = {
        "messages": state["conversation_for_generation"],
        "stream": state.get("stream", False),
    }

    if state.get("stream"):
        response = requests.post(
            f"http://{GENERATION_HOST}:{GENERATION_PORT}/generate",
            json=payload,
            stream=True,
            timeout=60,
        )

        response.raise_for_status()

        return {
            "answer_stream": response,
        }

    response = requests.post(
        f"http://{GENERATION_HOST}:{GENERATION_PORT}/generate",
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    return {
        "answer": response.json(),
        "answer_stream": None,
    }


def get_agent_tool_image(filename: str):
    response = requests.get(
        f"http://{GENERATION_HOST}:{GENERATION_PORT}/image/{filename}",
        stream=True,
        timeout=30,
    )

    return response