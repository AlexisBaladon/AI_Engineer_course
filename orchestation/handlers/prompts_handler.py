EXPERTISE_AREA = "the chess club Nau64"

system_prompt = """
You are a chatbot, expert in {expertise_area}.

The inputs you will recieve are:
- A list of documents.
- A query asking about information contained in them.

The output you should provide must satisfy the following requirements:
- It uses the current converstaion and documents as the only source of information.
- It uses urls provided in the prompt to point the user to the official website.
- It shows data the most visual way possible, including emojis or Markdown (tables, bulletpoints, titles, etc.).""".strip()

user_prompt = """
Query:
{query}

Documents:
{documents}
""".strip()

system_prompt = system_prompt.format(expertise_area=EXPERTISE_AREA)

def fill_user_prompt(
    query: str,
    documents: list[str],
    urls: list[str],
    user_prompt=user_prompt,
):
    if len(documents) != len(urls):
        raise ValueError(
            "documents and urls must have the same length"
        )

    # Build markdown document blocks
    document_blocks = []

    for idx, (doc, url) in enumerate(zip(documents, urls), start=1):
        block = f"""### Document [{idx}]\\nnSource: {url}\n\nContent: {doc}"""
        document_blocks.append(block)

    document_string = "\n\n".join(document_blocks)

    # Final structured markdown prompt
    final_user_prompt = user_prompt.format(
        query=query,
        documents=document_string,
    )

    return final_user_prompt