import datetime

import jwt


def create_token(username: str, encryption_secret_key: str) -> str:
    payload = {
        "user": username,
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(hours=2),
    }

    return jwt.encode(payload, encryption_secret_key, algorithm="HS256")


def _decode_token(token: str, encryption_secret_key: str):
    return jwt.decode(
        token,
        encryption_secret_key,
        algorithms=["HS256"],
    )


def get_current_user(cookies: dict, encryption_secret_key: str):
    token = cookies.get("auth_token")

    if not token:
        return None

    try:
        payload = _decode_token(token, encryption_secret_key)
        return payload["user"]
    except Exception:
        return None