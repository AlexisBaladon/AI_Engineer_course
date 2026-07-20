import json
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
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


def generate_and_trace(llm, messages, tools={}):

    response = llm.invoke(messages)

    while response.tool_calls:

        messages.append(response)

        for tool_call in response.tool_calls:
            for tool_name, tool_func in tools.items():
                if tool_call["name"] == tool_name:

                    result = tool_func.invoke(
                        tool_call["args"]
                    )

                    messages.append(
                        ToolMessage(
                            tool_call_id=tool_call["id"],
                            content=result,
                        )
                    )

        response = llm.invoke(messages)

    return {
        "content": response.content
    }, 200


def stream_response(llm, messages, tools=None):
    """
    Streams the response from the LLM while supporting tool calling.
    """

    if tools is None:
        tools = {}

    conversation = list(messages)

    while True:

        assistant_message = None

        # Stream one assistant turn
        for chunk in llm.stream(conversation):

            # Merge chunks together so tool_calls are reconstructed correctly
            if assistant_message is None:
                assistant_message = chunk
            else:
                assistant_message += chunk

            # Stream text immediately to the frontend
            if chunk.content:
                yield (
                    f"data: "
                    f"{json.dumps({'token': chunk.content})}"
                    f"\n\n"
                )

        # Nothing generated
        if assistant_message is None:
            break

        # Save assistant message into conversation
        conversation.append(assistant_message)

        # No tool requested -> we're done
        if not assistant_message.tool_calls:
            break

        # Execute every requested tool
        for tool_call in assistant_message.tool_calls:

            tool_name = tool_call["name"]

            if tool_name not in tools:
                raise ValueError(f"Unknown tool: {tool_name}")

            tool = tools[tool_name]

            result = tool.invoke(tool_call["args"])

            conversation.append(
                ToolMessage(
                    tool_call_id=tool_call["id"],
                    content=str(result),
                )
            )

    yield "data: [DONE]\n\n"