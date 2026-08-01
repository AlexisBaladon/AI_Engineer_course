DEFAULT_INAPPROPRIATE_RESPONSE = "La consulta realizada fue inapropiada. Vamos a bloquear tu cuenta temporalmente como medida de seguridad."
EXPERTISE_AREA = "the chess club Nau64"

system_prompt = """
You are a chatbot, expert in {expertise_area}.

The inputs you will recieve are:
- A list of documents obtained by matching the last query against our database.
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


def _handle_images(image_urls: list[str]):
    """
    This is one of the features only available for logged users,
    which consists in showing image urls to the model prompt.
    """
    image_block = ""

    if len(image_urls) > 0:
        image_block = "\n".join(
            f"- {image_url}"
            for image_url in image_urls
        )

        image_block = (
            "\n\n"
            "Images:\n"
            f"{image_block}"
        )

    return image_block


def fill_user_prompt(
    query: str,
    documents: list[str],
    urls: list[str],
    images: list[list[str]],
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

        image_block = _handle_images(image_urls)
        block += image_block

        document_blocks.append(block)

    document_string = "\n\n".join(document_blocks)

    final_user_prompt = user_prompt.format(
        query=query,
        documents=document_string,
    )

    return final_user_prompt


def get_last_user_message(user_conversation: list[dict]):
    return next(
        (
            message["content"]
            for message in reversed(user_conversation)
            if message["role"] == "user"
        ),
        None,
    )


def get_all_user_messages(user_conversation: list[dict]):
    return [
        message["content"]
        for message in user_conversation
        if message["role"] == "user"
    ]


def format_user_messages_for_filtering(user_messages: list[str]):
    # We asume that there's at least one message.
    formatted_user_messages = f"Message 1: {user_messages[0]}"

    for idx, user_message in enumerate(user_messages[1:], start=2):
        formatted_user_messages += f"\nMessage {idx}: {user_message}"

    return formatted_user_messages