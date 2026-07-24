from flask import Flask, jsonify, request
from langchain_openai import OpenAIEmbeddings

from retrieval_handler import (
    load_chunks,
    build_bm25_index,
    build_faiss_index,
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
bm25_index = build_bm25_index(chunks)
faiss_index = build_faiss_index(chunks)
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
)

@app.route("/retrieve", methods=["POST"])
def retrieve():
    data = request.get_json()
    query = data.get("query", None)
    top_k = data.get("top_k", 5)
    top_k = int(top_k)
    tracing_headers = data.get("tracing_headers", {})
    user_id = data.get("user_id", "default")

    if not query:
        return jsonify({
            "error": "query parameter is required"
        }), 400
    
    results = search(
        query=query,
        bm25=bm25_index,
        faiss_index=faiss_index,
        embeddings=embeddings,
        chunks=chunks,
        top_k=top_k,
        user_id=user_id,
        langsmith_extra={"parent": tracing_headers},
    )
    
    return jsonify(results), 200


@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)