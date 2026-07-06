from flask import Flask, jsonify, request, make_response
from flask_cors import CORS

from authentication_handler import (
    create_token,
    get_current_user,
)
from constants import (
    HOST,
    PORT,
    DEBUG,
    ADMIN_USER_USERNAME,
    ADMIN_USER_PASSWORD,
    ENCRYPTION_SECRET_KEY,
    HOOK_HOST,
    HOOK_PORT,
)

app = Flask(__name__)
CORS(app, origins=[f"http://{HOOK_HOST}:{HOOK_PORT}"], supports_credentials=True)


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if (
        username == ADMIN_USER_USERNAME
        and password == ADMIN_USER_PASSWORD
    ):
        token = create_token(username, encryption_secret_key=ENCRYPTION_SECRET_KEY)

        resp = make_response(
            jsonify({"message": "Login successful"})
        )

        resp.set_cookie(
            "auth_token",
            token,
            httponly=True, # HttpOnly cookie prevents JS access (important security)
            secure=False,  # TODO: set True in HTTPS production
            samesite="Lax",
        )

        return resp

    return jsonify(
        {"message": "Invalid credentials"}
    ), 401


@app.route("/logout", methods=["POST"])
def logout():
    resp = make_response(
        jsonify({"message": "Logged out"})
    )

    resp.delete_cookie("auth_token")

    return resp


@app.route("/auth/status", methods=["GET"])
def auth_status():
    user = get_current_user(request.cookies, encryption_secret_key=ENCRYPTION_SECRET_KEY)

    if user is None:
        return jsonify({
            "authenticated": False,
        }), 401

    return jsonify({
        "authenticated": True,
        "username": user,
    }), 200


@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG,
    )