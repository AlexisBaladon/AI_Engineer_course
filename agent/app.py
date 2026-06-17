from flask import Flask, jsonify, request
from langsmith import traceable
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

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


@traceable(run_type="llm", name="Generate Answer")
def generate_and_trace(user_prompt: str, system_prompt: str):
    if not user_prompt:
        return {
            "error": "user_query parameter is required"
        }, 400
    
    messages = [
        HumanMessage(content=user_prompt)
    ]

    if system_prompt is not None:
        system_message = SystemMessage(content=system_prompt)
        messages.append(system_message)

    response = llm.invoke(messages)

    return {
        "content": response.content
    }, 200


@app.route("/generate")
def generate():
    user_prompt = request.args.get("user_prompt", None)
    system_prompt = request.args.get("system_prompt", None)

    result, status_code = generate_and_trace(user_prompt, system_prompt)

    return jsonify(result), status_code


if __name__ == "__main__":
    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG,
    )