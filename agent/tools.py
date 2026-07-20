from langchain_core.tools import tool

from constants import TOOLS_IMAGES_DIR, BACKEND_ORIGIN

import chess
import chess.svg
import os
import uuid


def create_chess_board_image(moves: list[str], images_dir=TOOLS_IMAGES_DIR) -> str:
    board = chess.Board()

    try:
        for move in moves:
            board.push_san(move)
    except Exception as e:
        return f"Could not render chess position: {str(e)}"

    svg = chess.svg.board(
        board,
        lastmove=board.peek()
    )

    filename = f"{uuid.uuid4()}.svg"
    path = os.path.join(images_dir, filename)
    os.makedirs(images_dir, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)

    return {
        "type": "image",
        "url": f"image/{filename}"
    }


@tool
def create_chess_board_image_tool(moves: list[str], images_dir=TOOLS_IMAGES_DIR) -> str:
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

        Do NOT include move numbers.
        Do NOT concatenate multiple moves into one string.
        One SAN move per list element.
        Include only valid chess sequences.
    """
    chess_board_result = create_chess_board_image(moves, images_dir)

    if type(chess_board_result) == str:
        return chess_board_result
    
    chess_board_result["url"] = f"{BACKEND_ORIGIN}/{chess_board_result['url']}"

    return chess_board_result