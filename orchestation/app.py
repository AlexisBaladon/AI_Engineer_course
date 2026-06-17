from flask import Flask, jsonify, request
from langsmith import traceable
import requests

from constants import (
    HOST,
    PORT,
    DEBUG,
    RETRIEVAL_HOST,
    RETRIEVAL_PORT,
    GENERATION_HOST,
    GENERATION_PORT,
)
from handlers.prompts_handler import fill_user_prompt, system_prompt


app = Flask(__name__)


@traceable(name="Main chain")
def answer_query_and_trace(
    query: str,
) -> str:
    # Retrieve context
    # TODO: Add exceptions
    retrieval_response = requests.get(
        f"http://{RETRIEVAL_HOST}:{RETRIEVAL_PORT}/retrieve",
        params={"query": query},
        timeout=10,
    )
    retrieval_response.raise_for_status()
    retrieved_chunks = retrieval_response.json()

    # Format context
    documents = [chunk["chunk_text"] for chunk in retrieved_chunks]
    user_prompt = fill_user_prompt(query, documents)


    # Step 4: Generate answer
    generation_response = requests.get(
        f"http://{GENERATION_HOST}:{GENERATION_PORT}/generate",
        params={"user_prompt": user_prompt, "system_prompt": system_prompt},
        timeout=5,
    )
    generation_response.raise_for_status()

    return generation_response.json(), 200



@app.route("/run_chain")
def run_chain():
    query = request.args.get("query", None)
    result, status_code = answer_query_and_trace(query)
    
    return jsonify(result), status_code


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)