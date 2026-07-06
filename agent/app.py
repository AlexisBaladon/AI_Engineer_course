from flask import Flask, jsonify, request, Response, stream_with_context
from langchain_openai import ChatOpenAI
import json

from constants import HOST, PORT, DEBUG
from agent_handler import (
    build_messages,
    generate_and_trace,
    stream_response,
)

app = Flask(__name__)

llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
    streaming=True,
)


@app.route("/generate", methods=["POST"])
def generate():
    body = request.get_json(silent=True) or {}

    raw_messages = body.get("messages", [])
    stream = body.get("stream", False)

    if not raw_messages:
        return jsonify({
            "error": "messages is required"
        }), 400

    try:
        messages = build_messages(raw_messages)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    if stream:
        return Response(
            stream_with_context(stream_response(llm, messages)),
            mimetype="text/event-stream",
        )
    result, status_code = (generate_and_trace(llm, messages))

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
