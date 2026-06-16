from flask import Flask, jsonify, request
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


@app.route("/retrieve")
def retrieve():
    query = request.args.get("query", None)

    if not query:
        return jsonify({
            "error": "query parameter is required"
        }), 400

    results = search(
        query=query,
        bm25=bm25,
        chunks=chunks,
        top_k=3,
    )

    return jsonify(results)


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)