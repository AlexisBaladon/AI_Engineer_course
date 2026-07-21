from flask import Flask, jsonify, request
from langchain_openai import ChatOpenAI

from reasoning_handler import (
    judge_context,
    rewrite_query,
)

from constants import (
    HOST,
    PORT,
    DEBUG,
)


app = Flask(__name__)
judge_llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
)
query_rewriting_llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0.2,
)

def judge_query(query: str, chunks: list[dict], **kwargs):
    if query is None:
        return {
            "error": "query is a required attribute in the request"
        }, 400

    if chunks is None:
        return {
            "error": "chunks are a required attribute in the request"
        }, 400

    result = judge_context(
        query=query,
        chunks=chunks,
        llm=judge_llm,
        **kwargs,
    )

    return result, 200


def rewrite_query_request(query: str, chunks: list[dict], **kwargs):
    if query is None:
        return {
            "error": "query is a required attribute in the request"
        }, 400

    if chunks is None:
        return {
            "error": "chunks are a required attribute in the request"
        }, 400

    rewritten_query = rewrite_query(
        query=query,
        chunks=chunks,
        llm=query_rewriting_llm,
        **kwargs,
    )

    return {
        "query": rewritten_query
    }, 200


@app.route("/judge", methods=["POST"])
def judge():
    data = request.get_json()

    query = data.get("query")
    chunks = data.get("chunks")
    tracing_headers = data.get("tracing_headers")

    result, status_code = judge_query(
        query,
        chunks,
        langsmith_extra={"parent": tracing_headers}
    )

    return jsonify(result), status_code


@app.route("/rewrite", methods=["POST"])
def rewrite():
    data = request.get_json()

    query = data.get("query")
    chunks = data.get("chunks")
    tracing_headers = data.get("tracing_headers")

    result, status_code = rewrite_query_request(
        query,
        chunks,
        langsmith_extra={"parent": tracing_headers}
    )

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