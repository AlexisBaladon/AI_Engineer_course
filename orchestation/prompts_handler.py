from orchestation.mcp_adapters.image_mcp import handle_images_mcp


EXPERTISE_AREA = "the chess club Nau64"

system_prompt = """
You are a chatbot, expert in {expertise_area}.

The inputs you will recieve are:
- A list of documents, and additional information about them.
- A query asking about information contained in them.

The output you should provide must satisfy the following requirements:
- It uses the current converstaion and documents as the only source of information.
- It uses urls provided in the prompt to point the user to the official website.
- The user may or may not provide images in the prompt. If he does, you may want to add a couple of them in your response.
- It shows data the most visual way possible, including emojis or Markdown (tables, bulletpoints, titles, images, etc.).""".strip()

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
    images: list[list[str]],
    role: str,
    user_prompt=user_prompt,
):
    if len(documents) != len(urls):
        raise ValueError(
            "documents and urls must have the same length"
        )

    if len(documents) != len(images):
        raise ValueError(
            "documents and images must have the same length"
        )

    document_blocks = []

    for idx, (doc, url, image_urls) in enumerate(
        zip(documents, urls, images),
        start=1,
    ):
        block = (
            f"### Document [{idx}]\n\n"
            f"Source: {url}\n\n"
            f"Content:\n{doc}"
        )

        image_block = handle_images_mcp(role, image_urls)
        block += image_block

        document_blocks.append(block)

    document_string = "\n\n".join(document_blocks)

    final_user_prompt = user_prompt.format(
        query=query,
        documents=document_string,
    )

    return final_user_prompt