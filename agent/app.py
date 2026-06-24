from flask import Flask, jsonify, request, Response, stream_with_context
from langchain_core.messages import (
HumanMessage,
AIMessage,
SystemMessage,
)
from langchain_openai import ChatOpenAI
import json

from constants import HOST, PORT, DEBUG


app = Flask(__name__)

llm = ChatOpenAI(
model="gpt-4.1-mini",
temperature=0,
streaming=True,
)


def build_messages(raw_messages):
    messages = []

    for message in raw_messages:
        role = message.get("role")
        content = message.get("content", "")

        if role == "system":
            messages.append(
                SystemMessage(content=content)
            )

        elif role == "user":
            messages.append(
                HumanMessage(content=content)
            )

        elif role == "assistant":
            messages.append(
                AIMessage(content=content)
            )

        else:
            raise ValueError(
                f"Unsupported role: {role}"
            )

    return messages


def generate_and_trace(messages):
    response = llm.invoke(messages)

    return {
        "content": response.content
    }, 200


def stream_response(messages):
    for chunk in llm.stream(messages):
        if chunk.content:
            yield (
                f"data: "
                f"{json.dumps({'token': chunk.content})}"
                f"\n\n"
            )

    yield "data: [DONE]\n\n"


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
            stream_with_context(stream_response(messages)),
            mimetype="text/event-stream",
        )
    result, status_code = (generate_and_trace(messages))

    return jsonify(result), status_code


if __name__ == "__main__":
    app.run(
    host=HOST,
    port=PORT,
    debug=DEBUG,
)
