from typing import TypedDict
import requests

from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS
from langsmith import traceable
from langgraph.graph import StateGraph, START, END


from constants import (
    HOST,
    PORT,
    DEBUG,
    RETRIEVAL_HOST,
    RETRIEVAL_PORT,
    GENERATION_HOST,
    GENERATION_PORT,
)

from handlers.prompts_handler import (
    fill_user_prompt,
    system_prompt,
)


app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])


class RAGState(TypedDict):
    user_conversation: list[dict]
    stream: bool

    retrieved_chunks: list
    documents: list[str]

    conversation_for_generation: list[dict]
    answer: dict
    answer_stream: object


def get_last_message(user_conversation: list[dict]):
    return next(
        (
            message["content"]
            for message in reversed(user_conversation)
            if message["role"] == "user"
        ),
        None,
    )


@traceable(name="Retrieve Context")
def retrieve_node(state: RAGState):
    last_user_message = get_last_message(state["user_conversation"])

    retrieval_response = requests.get(
        f"http://{RETRIEVAL_HOST}:{RETRIEVAL_PORT}/retrieve",
        params={"query": last_user_message},
        timeout=10,
    )

    retrieval_response.raise_for_status()

    retrieved_chunks = retrieval_response.json()

    return {
        "retrieved_chunks": retrieved_chunks,
        "documents": [
            chunk["chunk_text"]
            for chunk in retrieved_chunks
        ],
    }


@traceable(name="Build Prompt")
def build_prompt_node(state: RAGState):
    last_user_message = get_last_message(state["user_conversation"])
    rag_prompt = fill_user_prompt(last_user_message, state["documents"])
    
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


@traceable(name="Generate Answer")
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


def build_graph():
    graph_builder = StateGraph(RAGState)
    graph_builder.add_node("retrieve", retrieve_node)
    graph_builder.add_node("build_prompt", build_prompt_node)
    graph_builder.add_node("generate", generate_node)
    graph_builder.add_edge(START, "retrieve")
    graph_builder.add_edge("retrieve", "build_prompt")
    graph_builder.add_edge("build_prompt", "generate")
    graph_builder.add_edge("generate", END)
    return graph_builder.compile()

rag_graph = build_graph()


@traceable(name="Main Chain")
def answer_query_and_trace(messages: list[str], stream: bool = False):
    result = rag_graph.invoke({
        "user_conversation": messages,
        "stream": stream,
    })

    if stream:
        return result["answer_stream"], None
    return result["answer"], 200


@app.route("/run_chain", methods=["POST"])
def run_chain():
    body = request.get_json()

    messages = body.get("messages", [])
    stream = body.get("stream", False)

    if stream:
        raw_response, _ = answer_query_and_trace(messages, stream=True)

        def generate_chunks():
            for chunk in raw_response.iter_content(chunk_size=None):
                if chunk:
                    yield chunk

        return Response(
            stream_with_context(generate_chunks()),
            content_type=raw_response.headers.get("Content-Type", "text/event-stream"),
        )

    result, status_code = answer_query_and_trace(messages, stream=False)
    return jsonify(result), status_code


if __name__ == "__main__":
    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG,
    )