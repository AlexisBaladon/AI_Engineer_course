from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import jwt
import datetime


from constants import (
    HOST,
    PORT,
    DEBUG,
    ADMIN_USER_USERNAME,
    ADMIN_USER_PASSWORD,
    ENCRYPTION_SECRET_KEY,
)

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"], supports_credentials=True)


def create_token(username: str) -> str:
    payload = {
        "user": username,
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(hours=2),
    }

    return jwt.encode(payload, ENCRYPTION_SECRET_KEY, algorithm="HS256")


def decode_token(token: str):
    return jwt.decode(
        token,
        ENCRYPTION_SECRET_KEY,
        algorithms=["HS256"],
    )


def get_current_user():
    token = request.cookies.get("auth_token")

    if not token:
        return None

    try:
        payload = decode_token(token)
        return payload["user"]
    except Exception:
        return None


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if (
        username == ADMIN_USER_USERNAME
        and password == ADMIN_USER_PASSWORD
    ):
        token = create_token(username)

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
    user = get_current_user()

    if user is None:
        return jsonify({
            "authenticated": False,
        }), 401

    return jsonify({
        "authenticated": True,
        "username": user,
    }), 200


if __name__ == "__main__":
    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG,
    )