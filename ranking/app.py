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


def rank_and_trace(query: str, chunks: list[dict], top_k=3, **kwargs):
    if query is None:
        return {
            "error": "query is a required attribute in the request"
        }, 400
    
    if chunks is None:
        return {
            "error": "chunks are a required attribute in the request"
        }, 400

    reranked_results = rerank_chunks(
        query,
        chunks,
        llm,
        **kwargs,
    )

    top_results = reranked_results[:top_k]

    return top_results, 200



@app.route("/rank", methods=["POST"])
def rank():
    data = request.get_json()
    query = data.get("query", None)
    chunks = data.get("chunks", None)
    top_k = data.get("top_k", 3)
    top_k = int(top_k)
    tracing_headers = data.get("tracing_headers")
    result, status_code = rank_and_trace(
        query, 
        chunks, 
        top_k, 
        langsmith_extra={"parent": tracing_headers}
    )
    
    return jsonify(result), status_code


@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)