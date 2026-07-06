import json
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
)

def build_messages(raw_messages):
    messages = []

    for message in raw_messages:
        role = message.get("role")
        content = message.get("content", "")

        if role == "system":
            messages.append(
                SystemMessage(content=content)
            )

        elif role == "user":
            messages.append(
                HumanMessage(content=content)
            )

        elif role == "assistant":
            messages.append(
                AIMessage(content=content)
            )

        else:
            raise ValueError(
                f"Unsupported role: {role}"
            )

    return messages


def generate_and_trace(llm, messages):
    response = llm.invoke(messages)

    return {
        "content": response.content
    }, 200


def stream_response(llm, messages):
    for chunk in llm.stream(messages):
        if chunk.content:
            yield (
                f"data: "
                f"{json.dumps({'token': chunk.content})}"
                f"\n\n"
            )

    yield "data: [DONE]\n\n"