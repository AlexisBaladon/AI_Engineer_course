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
    GENERATION_HOST,
    GENERATION_PORT,
)
from prompts_handler import (
    system_prompt,
)
from graph_handler import (
    build_graph,
)
from observability.langsmith_tracing import (
    traceable,
    get_current_run_tree,
    decode_stream,
)
from orchestration_controller import (
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
    role="user",
    stream: bool = False,
):
    tracing_tree = get_current_run_tree()
    tracing_headers = tracing_tree.to_headers()

    result = rag_graph.invoke(
        {
            "user_conversation": messages,
            "stream": stream,
            "role": role,
            "iteration": 0,
            "max_iterations": 3,
            "query_history": [],
        }
    )

    additional_information = {
        "system_prompt": system_prompt,
        "query": result["query"],
        "query_history": result.get("query_history", [result["query"]]),
        "iterations": result.get("iteration", 0),
        "role": result["role"],
        "retrieval_information": [
            {
                "chunk_text": chunk["chunk_text"],
                "lexical_score": chunk["lexical_score"],
                "semantic_score": chunk["semantic_score"],
            }
            for chunk in result["retrieved_chunks"]
        ],
    }

    if stream:
        chunk_generator = generate_chunks(
            result["answer_stream"],
            additional_information=additional_information,
            langsmith_extra={
                "parent": tracing_headers,
            },
        )
        return chunk_generator, None

    additional_information["answer"] = result["answer"]

    return additional_information, 200


@app.route("/run_chain", methods=["POST"])
def run_chain():
    body = request.get_json()

    messages = body.get("messages", [])
    role = body.get("role", "user")
    stream = body.get("stream", False)

    if stream:
        chunk_generator, _ = answer_query_and_trace(
            messages,
            role,
            stream=True,
        )

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