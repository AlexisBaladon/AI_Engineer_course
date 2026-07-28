import json
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)
from langsmith import traceable

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


def generate_and_trace(llm, messages, user_id="default", tool_mapping={}):
    llm = llm.bind(user=user_id)
    tool_functions = tool_mapping.values()
    llm = llm.bind_tools(tool_functions)

    response = llm.invoke(messages)

    while response.tool_calls:

        messages.append(response)

        for tool_call in response.tool_calls:
            for tool_name, tool_func in tool_mapping.items():
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


@traceable(type="llm", name="Agent")
def stream_response(llm, messages, user_id="default", tool_mapping=None, max_turns=10):
    """
    Streams the response from the LLM while supporting tool calling.
    """
    tool_mapping = tool_mapping or {}
    conversation = list(messages)

    if tool_mapping:
        llm = llm.bind_tools(list(tool_mapping.values()))
    llm = llm.bind(user=user_id)

    turns = 0

    while True:
        turns += 1
        if turns > max_turns:
            yield (
                f"data: "
                f"{json.dumps({'error': 'Max tool-calling turns exceeded.'})}"
                f"\n\n"
            )
            break

        assistant_message = None

        # Stream one assistant turn
        try:
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
        except Exception as e:
            yield (
                f"data: "
                f"{json.dumps({'error': f'LLM streaming failed: {e}'})}"
                f"\n\n"
            )
            break

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
            tool = tool_mapping.get(tool_name)

            if tool is None:
                conversation.append(
                    ToolMessage(
                        tool_call_id=tool_call["id"],
                        content=f"Error: unknown tool '{tool_name}'.",
                    )
                )
                continue

            try:
                # Pass the full tool_call so BaseTool.invoke returns a
                # correctly-formed ToolMessage (handles content_and_artifact, etc.)
                tool_message = tool.invoke(tool_call)
            except Exception as e:
                tool_message = ToolMessage(
                    tool_call_id=tool_call["id"],
                    content=f"Error executing tool '{tool_name}': {e}",
                )

            conversation.append(tool_message)

    yield "data: [DONE]\n\n"