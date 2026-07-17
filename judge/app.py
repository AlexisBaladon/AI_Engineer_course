from flask import Flask, jsonify, request
from openai import OpenAI

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
openai_client = OpenAI()


def judge_query(query: str, chunks: list[dict]):
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
        openai_client=openai_client,
    )

    return result, 200


def rewrite_query_request(query: str, chunks: list[dict]):
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
        openai_client=openai_client,
    )

    return {
        "query": rewritten_query
    }, 200


@app.route("/judge", methods=["POST"])
def judge():
    data = request.get_json()

    query = data.get("query")
    chunks = data.get("chunks")

    result, status_code = judge_query(
        query,
        chunks,
    )

    return jsonify(result), status_code


@app.route("/rewrite", methods=["POST"])
def rewrite():
    data = request.get_json()

    query = data.get("query")
    chunks = data.get("chunks")

    result, status_code = rewrite_query_request(
        query,
        chunks,
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