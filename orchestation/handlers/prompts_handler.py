EXPERTISE_AREA = "the chess club Nau64"

system_prompt = """
You are a chatbot, expert in {expertise_area}.

The inputs you will recieve are:
- A list of documents.
- A query asking about information contained in them.

The output you should provide is an answer that uses the inputs as the only source of information, \
while following good costumer service practices.
""".strip()

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
    user_prompt=user_prompt,
):
    # Document
    document_string = ""
    first_document_index = 1
    document_length = len(documents)
    for idx, document in enumerate(documents, start=first_document_index):
        document_string += f"{idx}. {document}"
        if idx < document_length:
            document_string += "\n"

    # Final string
    final_user_prompt = user_prompt.format(
        query=query, 
        documents=document_string
    )
    return final_user_prompt