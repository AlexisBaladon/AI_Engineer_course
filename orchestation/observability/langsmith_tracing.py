import json

from langsmith import traceable, get_current_run_tree


def decode_stream(tokens: list[str]):
    tokens = [token.replace('data: {"token": "', '{"token": "') for token in tokens]
    tokens = [token.replace('"}\n\n', '"}') for token in tokens]
    tokens = [json.loads(token)["token"] for token in tokens if "[DONE]" not in token]
    tokens = [token.replace('data: [DONE]\n\n', "") for token in tokens]
    return "".join(tokens)