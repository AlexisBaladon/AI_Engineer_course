# -------------------------
# ORCHESTRATION
# -------------------------
from agent import generate_response


def handle_request(role: str, messages: list[str]):
    # Decide which tools this user may use
    tools = []

    if role == "authenticated_user":
        tools = [
            "image_generation_tool",
        ]
        
    return generate_response(
        messages=messages,
        tools=tools,
    )


# -------------------------
# AGENT
# -------------------------
from langchain_openai import ChatOpenAI
from mcp_adapter import create_image_tool


all_tools = {"create_image_tool": create_image_tool}

def generate_response(messages, tools):
    llm = ChatOpenAI(...)
    selected_tools = {tool_name: all_tools[tool_name] for tool_name in all_tools}
    llm_with_tools = llm.bind_tools(selected_tools)
    return llm_with_tools.invoke(messages)


# -------------------------
# MCP ADAPTER
# -------------------------
from langchain.tools import tool
from business_logic import create_image

@tool
def create_image_tool(user_inputs: list[str]):
    # Validate inputs if necessary
    result = create_image(user_inputs)
    # Adapt / postprocess outputs if necessary
    return result

# -------------------------
# BUSINESS LOGIC
# -------------------------
import image_library

def create_image(user_inputs):
    image = image_library.generate_image(user_inputs)
    return image