from pathlib import Path

BEGIN_MARKER = "<!-- BEGIN AUTO-GENERATED EVALUATION -->"
END_MARKER = "<!-- END AUTO-GENERATED EVALUATION -->"


def merge_evaluation_readme(
    evaluation_readme: str | Path,
    parent_readme: str | Path,
):
    """
    Inserts or updates the evaluation report inside the parent README.
    """

    evaluation_readme = Path(evaluation_readme)
    parent_readme = Path(parent_readme)

    evaluation = evaluation_readme.read_text(encoding="utf-8").strip()

    generated_section = (
        f"{BEGIN_MARKER}\n\n"
        f"{evaluation}\n\n"
        f"{END_MARKER}\n"
    )

    if parent_readme.exists():
        parent = parent_readme.read_text(encoding="utf-8")
    else:
        parent = ""

    if BEGIN_MARKER in parent and END_MARKER in parent:
        start = parent.index(BEGIN_MARKER)
        end = parent.index(END_MARKER) + len(END_MARKER)

        updated = (
            parent[:start]
            + generated_section
            + parent[end:]
        )
    else:
        if parent and not parent.endswith("\n"):
            parent += "\n"

        updated = parent.rstrip() + "\n\n" + generated_section

    parent_readme.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    merge_evaluation_readme(
    "./README.md",
    "../README.md",
)