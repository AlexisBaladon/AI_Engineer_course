from flask import Flask, jsonify, request
from langsmith import traceable
from langchain_core.messages import HumanMessage
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

from constants import (
    HOST,
    PORT,
    DEBUG,
)


app = Flask(__name__)


@traceable(run_type="tool", name="Retrieve Context")
def generate_and_trace(query: str):
    if not query:
        return {
            "error": "query parameter is required"
        }, 400

    responses = ["Hello, I am a dummy AI!", "What else do you need help with?"]
    fake_model = GenericFakeChatModel(messages=iter(responses))
    response = fake_model.invoke([HumanMessage(content=query)])
    response = {"content": response.content}

    return response, 200



@app.route("/generate")
def generate():
    query = request.args.get("query", None)
    result, status_code = generate_and_trace(query)
    
    return jsonify(result), status_code


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)