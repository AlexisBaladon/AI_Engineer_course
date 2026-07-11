import requests

from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS

from constants import (
    HOST,
    PORT,
    DEBUG,
    RETRIEVAL_HOST,
    RETRIEVAL_PORT,
    RANKING_HOST,
    RANKING_PORT,
    GENERATION_HOST,
    GENERATION_PORT,
    HOOK_HOST,
    HOOK_PORT,
)
from prompts_handler import (
    fill_user_prompt,
    system_prompt,
)
from graph_handler import (
    RAGState,
    build_graph,
)
from observability.langsmith_tracing import traceable
import observability.arize_tracing


app = Flask(__name__)
CORS(app, origins=[f"http://{HOOK_HOST}:{HOOK_PORT}"])


def get_last_message(user_conversation: list[dict]):
    return next(
        (
            message["content"]
            for message in reversed(user_conversation)
            if message["role"] == "user"
        ),
        None,
    )


def retrieve_node(state: RAGState):
    last_user_message = get_last_message(state["user_conversation"])

    retrieval_response = requests.get(
        f"http://{RETRIEVAL_HOST}:{RETRIEVAL_PORT}/retrieve",
        params={"query": last_user_message, "top_k": 5},
        timeout=30,
    )

    retrieval_response.raise_for_status()

    retrieved_chunks = retrieval_response.json()

    return {
        "query": last_user_message,
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


rag_graph = build_graph(
    retrieve_node,
    rank_node,
    build_prompt_node,
    generate_node,
)


@traceable(name="Main Chain")
def answer_query_and_trace(messages: list[str], role="user", stream: bool = False):
    result = rag_graph.invoke({
        "user_conversation": messages,
        "stream": stream,
        "role": role,
    })

    if stream:
        return result["answer_stream"], None
    return result["answer"], 200


@app.route("/run_chain", methods=["POST"])
def run_chain():
    body = request.get_json()

    messages = body.get("messages", [])
    role = body.get("role", "user")
    stream = body.get("stream", False)

    if stream:
        raw_response, _ = answer_query_and_trace(messages, role, stream=True)

        def generate_chunks():
            for chunk in raw_response.iter_content(chunk_size=None):
                if chunk:
                    yield chunk

        return Response(
            stream_with_context(generate_chunks()),
            content_type=raw_response.headers.get("Content-Type", "text/event-stream"),
        )

    result, status_code = answer_query_and_trace(messages, role, stream=False)
    return jsonify(result), status_code


@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG,
    )