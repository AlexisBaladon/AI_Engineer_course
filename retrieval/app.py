from flask import Flask, jsonify, request
from openai import OpenAI

from handlers.retrieval_handler import (
    load_chunks,
    build_bm25_index,
    search,
)
from constants import (
    CHUNKED_DATA_PATH,
    IMAGES_PATH,
    HOST,
    PORT,
    DEBUG,
)


app = Flask(__name__)
chunks = load_chunks(CHUNKED_DATA_PATH, IMAGES_PATH)
bm25 = build_bm25_index(chunks)
openai_client = OpenAI()


@app.route("/retrieve")
def retrieve():
    query = request.args.get("query", None)
    top_k = request.args.get("top_k", 5)
    top_k = int(top_k)

    if not query:
        return jsonify({
            "error": "query parameter is required"
        }), 400
    
    results = search(
        query=query,
        bm25=bm25,
        openai_client=openai_client,
        chunks=chunks,
        top_k=top_k,
    )
    
    return jsonify(results), 200


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)