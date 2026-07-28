import chess
import chess.svg

from constants import TOOLS_IMAGES_DIR

import os
import uuid


def create_chess_board_image(
    moves: list[str], 
    images_dir=TOOLS_IMAGES_DIR, 
    max_length=50,
) -> str:
    board = chess.Board()

    moves = moves[:max_length]

    # Can raise an exception
    for move in moves:
        board.push_san(move)

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
        "url": filename,
    }