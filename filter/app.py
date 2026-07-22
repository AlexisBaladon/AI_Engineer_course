from flask import (
    Flask, 
    jsonify, 
    request,
)
from openai import OpenAI

from constants import HOST, PORT, DEBUG
from filter_handler import (
    filter_query,
    QueryFilter
)


app = Flask(__name__)
client = OpenAI()
llm = QueryFilter(client)


@app.route("/filter", methods=["POST"])
def generate():
    body = request.get_json(silent=True) or {}

    query = body.get("query", "")
    tracing_headers = body.get("tracing_headers", {})

    if not query:
        return jsonify({
            "error": "query is required"
        }), 400

    try:
        query_analysis = filter_query(
            query, 
            llm, 
            langsmith_extra={"parent": tracing_headers}
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(query_analysis), 200


@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(
    host=HOST,
    port=PORT,
    debug=DEBUG,
)
