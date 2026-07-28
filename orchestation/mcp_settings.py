CHESS_BOARD_CREATION_TOOL = "create_chess_board_image_tool" 
ADMIN_ROLE = "admin"


def define_mcp_settings(state: dict) -> dict:
    role = state["role"]
    tools = []

    if role == ADMIN_ROLE:
        tools = [
            CHESS_BOARD_CREATION_TOOL,
        ]

    return {
        "tools": tools
    }