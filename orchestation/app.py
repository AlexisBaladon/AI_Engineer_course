import json

import requests
from flask import (
    Flask,
    jsonify,
    request,
    Response,
    stream_with_context,
    abort,
)
from flask_cors import CORS

from constants import (
    HOST,
    PORT,
    DEBUG,
    HOOK_HOST,
    HOOK_PORT,
)
from prompts_handler import (
    system_prompt,
)
from graph_handler import (
    build_graph,
)
from observability.langsmith_tracing import (
    traceable,
    get_tracing_headers,
    decode_stream,
)
from utils import get_additional_information
from mcp_settings import define_mcp_settings 
from orchestration_controller import (
    filter_node,
    retrieve_node,
    rank_node,
    judge_context_node,
    rewrite_query_node,
    build_prompt_node,
    generate_node,
    get_agent_tool_image,
)
from observability.arize_tracing import tracer_provider as _


app = Flask(__name__)
CORS(
    app,
    origins=[f"http://{HOOK_HOST}:{HOOK_PORT}"],
)

rag_graph = build_graph(
    filter_node,
    define_mcp_settings,
    retrieve_node,
    rank_node,
    judge_context_node,
    rewrite_query_node,
    build_prompt_node,
    generate_node,
)


@traceable(
    run_type="llm",
    name="Final response",
    reduce_fn=decode_stream,
)
def generate_chunks(answer_stream, additional_information: dict):
    for chunk in answer_stream.iter_content(chunk_size=None):
        if chunk:
            yield chunk.decode()

    yield json.dumps(additional_information)


@traceable(name="Main Chain")
def answer_query_and_trace(
    messages: list[str],
    user_id: str,
    role="user",
    stream: bool = False,
):
    result = rag_graph.invoke(
        {
            "user_conversation": messages,
            "stream": stream,
            "role": role,
            "iteration": 0,
            "max_iterations": 1,
            "query_history": [],
            "user_id": user_id,
        }
    )

    additional_information = get_additional_information(result, system_prompt)

    status_code = 500 if result["is_inappropriate"] else 200

    if stream:
        tracing_headers = get_tracing_headers()
        chunk_generator = generate_chunks(
            result["answer_stream"],
            additional_information=additional_information,
            langsmith_extra={
                "parent": tracing_headers,
            },
        )
        return chunk_generator, status_code

    additional_information["answer"] = result["answer"]

    return additional_information, status_code


@app.route("/run_chain", methods=["POST"])
def run_chain():
    body = request.get_json()

    messages = body.get("messages", [])
    role = body.get("role", "user")
    stream = body.get("stream", False)
    user_id = body.get("user_id", "default")

    result, status_code = answer_query_and_trace(
        messages,
        user_id,
        role,
        stream=stream,
    )

    if stream:
        chunk_generator = result
        return Response(
            stream_with_context(chunk_generator),
            content_type="text/event-stream",
        )

    result, status_code = answer_query_and_trace(
        messages,
        role,
        stream=False,
    )

    return jsonify(result), status_code


@app.route("/image/<path:filename>", methods=["GET"])
def get_image(filename):
    """
    Retrieves an image from the agent service and returns it to the client.
    """

    try:
        response = get_agent_tool_image(filename)
    except requests.RequestException:
        abort(502)

    if response.status_code != 200:
        abort(response.status_code)

    return Response(
        response.iter_content(chunk_size=8192),
        content_type=response.headers.get(
            "Content-Type",
            "image/svg+xml",
        ),
    )


@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG,
    )