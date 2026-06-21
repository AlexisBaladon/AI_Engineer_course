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
    query: str
    stream: bool
    retrieved_chunks: list
    documents: list[str]
    user_prompt: str
    answer: dict
    answer_stream: object


@traceable(name="Retrieve Context")
def retrieve_node(state: RAGState):
    retrieval_response = requests.get(
        f"http://{RETRIEVAL_HOST}:{RETRIEVAL_PORT}/retrieve",
        params={"query": state["query"]},
        timeout=10,
    )

    retrieval_response.raise_for_status()
    retrieved_chunks = retrieval_response.json()

    return {
        "retrieved_chunks": retrieved_chunks,
        "documents": [chunk["chunk_text"] for chunk in retrieved_chunks],
    }


@traceable(name="Build Prompt")
def build_prompt_node(state: RAGState):
    return {
        "user_prompt": fill_user_prompt(
            state["query"],
            state["documents"],
        )
    }


@traceable(name="Generate Answer")
def generate_node(state: RAGState):
    params = {
        "user_prompt": state["user_prompt"],
        "system_prompt": system_prompt,
        "stream": state.get("stream", False),
    }

    if state.get("stream"):
        generation_response = requests.get(
            f"http://{GENERATION_HOST}:{GENERATION_PORT}/generate",
            params=params,
            stream=True,
            timeout=60,
        )
        generation_response.raise_for_status()

        return {"answer_stream": generation_response}

    else:
        generation_response = requests.get(
            f"http://{GENERATION_HOST}:{GENERATION_PORT}/generate",
            params=params,
            timeout=30,
        )
        generation_response.raise_for_status()

        return {"answer": generation_response.json(), "answer_stream": None}


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
def answer_query_and_trace(query: str, stream: bool = False):
    result = rag_graph.invoke({
        "query": query,
        "stream": stream,
    })

    if stream:
        return result["answer_stream"], None
    return result["answer"], 200


@app.route("/run_chain")
def run_chain():
    query = request.args.get("query")
    stream = request.args.get("stream", "false").lower() == "true"

    if not query:
        return jsonify({"error": "query parameter is required"}), 400

    if stream:
        raw_response, _ = answer_query_and_trace(query, stream=True)

        def generate_chunks():
            for chunk in raw_response.iter_content(chunk_size=None):
                if chunk:
                    yield chunk

        return Response(
            stream_with_context(generate_chunks()),
            content_type=raw_response.headers.get("Content-Type", "text/event-stream"),
        )

    result, status_code = answer_query_and_trace(query, stream=False)
    return jsonify(result), status_code


if __name__ == "__main__":
    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG,
    )