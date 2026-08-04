import json
import os
from datetime import UTC, datetime


def save_conversation(
    username: str,
    conversation_id: int | str,
    conversation: list[dict],
    additional_information: dict,
    save_dir: str,
):
    os.makedirs(save_dir, exist_ok=True)

    path = os.path.join(save_dir, "persistence.json")

    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                database = json.load(f)
        except (json.JSONDecodeError, OSError):
            database = {}
    else:
        database = {}

    database.setdefault(username, {})

    now = datetime.now(UTC).isoformat()

    conversation_id = str(conversation_id)

    created_at = (
        database[username]
        .get(conversation_id, {})
        .get("created_at", now)
    )

    database[username][conversation_id] = {
        "created_at": created_at,
        "updated_at": now,
        "conversation": conversation,
        **additional_information,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            database,
            f,
            indent=4,
            ensure_ascii=False,
        )


def load_user_conversations(
    username: str,
    save_dir: str,
):
    path = os.path.join(save_dir, "persistence.json")

    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf8") as f:
        data = json.load(f)

    user_data = data.get(username)

    if user_data is None:
        return {}

    user_conversations = {}

    try:
        for conversation_id in list(user_data):
            user_conversations[conversation_id] = user_data[conversation_id]["conversation"]
    except KeyError:
        return {} 

    return user_conversations