from typing import TypedDict
import requests

from flask import Flask, jsonify, request
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
    retrieved_chunks: list
    documents: list[str]
    user_prompt: str
    answer: dict


@traceable(name="Retrieve Context")
def retrieve_node(state: RAGState):
    # TODO: Handle exceptions
    retrieval_response = requests.get(
        f"http://{RETRIEVAL_HOST}:{RETRIEVAL_PORT}/retrieve",
        params={"query": state["query"]},
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
    return {
        "user_prompt": fill_user_prompt(
            state["query"],
            state["documents"],
        )
    }


@traceable(name="Generate Answer")
def generate_node(state: RAGState):
    # TODO: Handle exceptions
    generation_response = requests.get(
        f"http://{GENERATION_HOST}:{GENERATION_PORT}/generate",
        params={
            "user_prompt": state["user_prompt"],
            "system_prompt": system_prompt,
        },
        timeout=5,
    )

    generation_response.raise_for_status()

    return {
        "answer": generation_response.json()
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
def answer_query_and_trace(query: str):
    result = rag_graph.invoke({
        "query": query,
    })

    return result["answer"], 200


@app.route("/run_chain")
def run_chain():
    query = request.args.get("query")

    if not query:
        return jsonify({
            "error": "query parameter is required"
        }), 400

    result, status_code = answer_query_and_trace(query)

    return jsonify(result), status_code


if __name__ == "__main__":
    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG,
    )