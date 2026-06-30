import requests

from flask import Flask, request, Response, stream_with_context
from flask_cors import CORS


from constants import (
    HOST,
    PORT,
    DEBUG,
    AUTHENTICATION_HOST,
    AUTHENTICATION_PORT,
    ORCHESTRATION_HOST,
    ORCHESTRATION_PORT,
    FRONTEND_HOST,
    FRONTEND_PORT,
    ADMIN_ROLE,
    USER_ROLE,
)


app = Flask(__name__)
CORS(app, origins=[f"http://{FRONTEND_HOST}:{FRONTEND_PORT}"], supports_credentials=True)


@app.route("/login", methods=["POST"])
def login():

    response = requests.post(
        f"http://{AUTHENTICATION_HOST}:{AUTHENTICATION_PORT}/login",
        json=request.get_json(),
    )

    flask_response = Response(
        response.content,
        status=response.status_code,
        content_type=response.headers.get("Content-Type"),
    )

    if "Set-Cookie" in response.headers:
        flask_response.headers["Set-Cookie"] = response.headers["Set-Cookie"]

    return flask_response


@app.route("/logout", methods=["POST"])
def logout():

    response = requests.post(
        f"http://{AUTHENTICATION_HOST}:{AUTHENTICATION_PORT}/logout",
        cookies=request.cookies,
    )

    flask_response = Response(
        response.content,
        status=response.status_code,
        content_type=response.headers.get("Content-Type"),
    )

    if "Set-Cookie" in response.headers:
        flask_response.headers["Set-Cookie"] = response.headers["Set-Cookie"]

    return flask_response


@app.route("/auth/status", methods=["GET"])
def auth_status():

    response = requests.get(
        f"http://{AUTHENTICATION_HOST}:{AUTHENTICATION_PORT}/auth/status",
        cookies=request.cookies,
    )

    return Response(
        response.content,
        status=response.status_code,
        content_type=response.headers.get("Content-Type"),
    )


@app.route("/chat", methods=["POST"])
def chat():

    body = request.get_json()

    stream = body.get("stream", False)

    auth = requests.get(
        f"http://{AUTHENTICATION_HOST}:{AUTHENTICATION_PORT}/auth/status",
        cookies=request.cookies,
    )

    role = USER_ROLE

    if auth.status_code == 200:
        role = ADMIN_ROLE

    body["role"] = role

    if stream:
        response = requests.post(
            f"http://{ORCHESTRATION_HOST}:{ORCHESTRATION_PORT}/run_chain",
            json=body,
            stream=True,
        )

        def generate():
            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    yield chunk

        return Response(
            stream_with_context(generate()),
            content_type=response.headers.get(
                "Content-Type",
                "text/event-stream",
            ),
        )

    response = requests.post(
        f"http://{ORCHESTRATION_HOST}:{ORCHESTRATION_PORT}/run_chain",
        json=body,
    )

    return Response(
        response.content,
        status=response.status_code,
        content_type=response.headers.get("Content-Type"),
    )


if __name__ == "__main__":
    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG,
    )