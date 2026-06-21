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
def retrieve_and_trace(query: str, top_k=3, lexical_weight=0.5, semantic_weight=0.5):
    if not query:
        return {
            "error": "query parameter is required"
        }, 400

    results = search(
        query=query,
        bm25=bm25,
        openai_client=openai_client,
        chunks=chunks,
        top_k=top_k,
        lexical_weight=lexical_weight,
        semantic_weight=semantic_weight,
    )

    return results, 200



@app.route("/retrieve")
def retrieve():
    query = request.args.get("query", None)
    top_k = request.args.get("top_k", 3)
    lexical_weight = request.args.get("lexical_weight", 0.5)
    semantic_weight = request.args.get("semantic_weight", 0.5)
    result, status_code = retrieve_and_trace(query, top_k, lexical_weight, semantic_weight)
    
    return jsonify(result), status_code


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)