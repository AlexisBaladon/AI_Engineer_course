from flask import Flask, jsonify, request
from langchain_openai import ChatOpenAI

from reranking_handler import (
    rerank_chunks,
)

from constants import (
    HOST,
    PORT,
    DEBUG,
)


app = Flask(__name__)
llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
)


@app.route("/rank", methods=["POST"])
def rank():
    data = request.get_json()
    query = data.get("query", None)
    chunks = data.get("chunks", None)
    top_k = data.get("top_k", 3)
    top_k = int(top_k)
    tracing_headers = data.get("tracing_headers")
    user_id = data.get("user_id", "default")

    if query is None:
        return jsonify({
            "error": "query is a required attribute in the request"
        }), 400
    
    if chunks is None:
        return jsonify({
            "error": "chunks are a required attribute in the request"
        }), 400

    reranked_results = rerank_chunks(
        query,
        chunks,
        user_id,
        llm,
        langsmith_extra={"parent": tracing_headers}
    )

    top_results = reranked_results[:top_k]
    
    return jsonify(top_results), 200


@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)