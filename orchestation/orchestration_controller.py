import requests

from conversation_handler import (
    fill_user_prompt,
    system_prompt,
    format_user_messages_for_filtering,
    get_all_user_messages,
    get_last_user_message,
    DEFAULT_INAPPROPRIATE_RESPONSE
)
from observability.langsmith_tracing import get_tracing_headers
from constants import (
    FILTER_HOST,
    FILTER_PORT,
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


class StaticResponseStream:
    def __init__(self, response: str):
        self.response = response

    def iter_content(self, chunk_size=None):
        response = f'data: {{"token": "{self.response}"}}\n\n'
        yield response.encode("utf-8")

        yield "data: [DONE]\n\n".encode("utf-8")


def filter_node(state: RAGState):
    tracing_headers = get_tracing_headers()
    query = state.get("query")
    user_id = state.get("user_id")

    if query is None:
        query = get_last_user_message(state["user_conversation"])

    all_user_messages = get_all_user_messages(state["user_conversation"])
    formatted_user_messages = format_user_messages_for_filtering(all_user_messages)
    
    payload = {
        "query": formatted_user_messages,
        "tracing_headers": tracing_headers,
        "user_id": user_id,
    }

    filter_response = requests.post(
        f"http://{FILTER_HOST}:{FILTER_PORT}/filter",
        json=payload,
        timeout=30,
    )
    filter_response.raise_for_status()
    filter_information = filter_response.json()
    is_inappropriate = filter_information["is_inappropriate"]

    extra_results = {} 
    if is_inappropriate:
        extra_results["answer"] = DEFAULT_INAPPROPRIATE_RESPONSE
        extra_results["answer_stream"] = StaticResponseStream(DEFAULT_INAPPROPRIATE_RESPONSE)

    return {
        "query": query,
        "is_inappropriate": is_inappropriate,
        **extra_results,
    }


def retrieve_node(state: RAGState):
    tracing_headers = get_tracing_headers()
    query = state.get("query")
    user_id = state.get("user_id")

    payload = {
        "query": query,
        "top_k": 10,
        "tracing_headers": tracing_headers,
        "user_id": user_id,
    }

    retrieval_response = requests.post(
        f"http://{RETRIEVAL_HOST}:{RETRIEVAL_PORT}/retrieve",
        json=payload,
        timeout=30,
    )

    retrieval_response.raise_for_status()

    retrieved_chunks = retrieval_response.json()

    return {
        "query": query,
        "retrieved_chunks": retrieved_chunks,
    }


def rank_node(state: RAGState):
    tracing_headers = get_tracing_headers()
    user_id = state.get("user_id")

    payload = {
        "query": state["query"],
        "chunks": state["retrieved_chunks"],
        "top_k": 3,
        "tracing_headers": tracing_headers,
        "user_id": user_id,
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
    tracing_headers = get_tracing_headers()
    user_id = state.get("user_id")

    payload = {
        "query": state["query"],
        "chunks": state["retrieved_chunks"],
        "tracing_headers": tracing_headers,
        "user_id": user_id,
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
    tracing_headers = get_tracing_headers()
    user_id = state.get("user_id")

    payload = {
        "query": state["query"],
        "chunks": state["retrieved_chunks"],
        "tracing_headers": tracing_headers,
        "user_id": user_id,
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
    chunks = state["retrieved_chunks"]
    documents = [chunk["chunk_text"] for chunk in chunks]
    images = [chunk["images"] for chunk in chunks]
    urls = [chunk["url"] for chunk in chunks]

    rag_prompt = fill_user_prompt(
        state["query"],
        documents,
        urls,
        images,
    )

    conversation_for_generation = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    conversation_for_generation.extend(
        state["user_conversation"][:-1]
    )

    conversation_for_generation.append(
        {
            "role": "user",
            "content": rag_prompt,
        }
    )

    return {
        "conversation_for_generation": conversation_for_generation,
    }


def generate_node(state: RAGState):
    tracing_headers = get_tracing_headers()
    user_id = state.get("user_id")
    allowed_tools = state.get("tools")

    payload = {
        "messages": state["conversation_for_generation"],
        "stream": state.get("stream", False),
        "tracing_headers": tracing_headers,
        "user_id": user_id,
        "tools": allowed_tools,
    }

    if state.get("stream"):
        response = requests.post(
            f"http://{GENERATION_HOST}:{GENERATION_PORT}/generate",
            json=payload,
            stream=True,
            timeout=120,
        )

        response.raise_for_status()

        return {
            "answer_stream": response,
        }

    response = requests.post(
        f"http://{GENERATION_HOST}:{GENERATION_PORT}/generate",
        json=payload,
        timeout=120,
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