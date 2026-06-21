from flask import Flask, jsonify, request, Response, stream_with_context
from langsmith import traceable
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import json

from constants import HOST, PORT, DEBUG

app = Flask(__name__)

llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
    streaming=True,
)


def build_messages(user_prompt, system_prompt):
    messages = []

    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))

    messages.append(HumanMessage(content=user_prompt))

    return messages


@traceable(run_type="llm", name="Generate Answer")
def generate_and_trace(user_prompt: str, system_prompt: str):
    if not user_prompt:
        return {"error": "user_query parameter is required"}, 400

    messages = build_messages(user_prompt, system_prompt)

    response = llm.invoke(messages)

    return {"content": response.content}, 200


def stream_response(messages):
    for chunk in llm.stream(messages):
        if chunk.content:
            yield f"data: {json.dumps({'token': chunk.content})}\n\n"

    yield "data: [DONE]\n\n"


@app.route("/generate")
def generate():
    user_prompt = request.args.get("user_prompt", None)
    system_prompt = request.args.get("system_prompt", None)
    stream = request.args.get("stream", "false").lower() == "true"

    if not user_prompt:
        return jsonify({"error": "user_prompt is required"}), 400

    messages = build_messages(user_prompt, system_prompt)

    if stream:
        return Response(
            stream_with_context(stream_response(messages)),
            mimetype="text/event-stream"
        )

    result, status_code = generate_and_trace(user_prompt, system_prompt)
    return jsonify(result), status_code


if __name__ == "__main__":
    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG,
    )