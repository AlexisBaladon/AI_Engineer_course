from langchain.tools import tool

from constants import BACKEND_ORIGIN

from agent.logic import (
    create_chess_board_image,
)


@tool
def create_chess_board_image_tool(moves: list[str]) -> str:
    """
    Creates an SVG image of a chess position.

        Parameters:
            moves: A list where EACH ELEMENT is a SINGLE move in SAN
            (Standard Algebraic Notation).

        Correct examples:
            ["e4", "e5", "Nf3", "Nc6", "Bb5"]

            ["d4", "Nf6", "c4", "g6", "Nc3"]

        Incorrect examples:
            ["1. e4 e5 2. Nf3 Nc6 3. Bb5"]

            ["e4 e5 Nf3 Nc6"]

            ["1.e4", "1...e5", "2.Nf3"]
    """
    try:
        chess_board_result = create_chess_board_image(moves)
    except Exception as e:
        return {
            "success": False,
            "result": f"There was an error generating this particular image: {e}."
        }

    # Postprocess output.
    chess_board_result["url"] = f"{BACKEND_ORIGIN}/image/{chess_board_result['url']}"

    return {
        "success": True,
        "result": chess_board_result,
    }


all_tools = {"create_chess_board_image_tool": create_chess_board_image_tool}
