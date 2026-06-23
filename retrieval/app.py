from flask import Flask, jsonify, request
from langsmith import traceable
from openai import OpenAI

from handlers.retrieval_handler import (
    load_chunks,
    build_bm25_index,
    search,
)
from constants import (
    CHUNKED_DATA_PATH,
    HOST,
    PORT,
    DEBUG,
)


app = Flask(__name__)
chunks = load_chunks(CHUNKED_DATA_PATH)
bm25 = build_bm25_index(chunks)
openai_client = OpenAI()


@traceable(run_type="tool", name="Retrieve Context")
def retrieve_and_trace(query: str, reranking_candidate_count=10, top_k=3):
    if not query:
        return {
            "error": "query parameter is required"
        }, 400

    results = search(
        query=query,
        bm25=bm25,
        openai_client=openai_client,
        chunks=chunks,
        candidate_count=reranking_candidate_count,
        top_k=top_k,
    )

    return results, 200



@app.route("/retrieve")
def retrieve():
    query = request.args.get("query", None)
    reranking_candidate_count = request.args.get("reranking_candidate_count", 10)
    top_k = request.args.get("top_k", 3)
    result, status_code = retrieve_and_trace(query, reranking_candidate_count, top_k)
    
    return jsonify(result), status_code


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)