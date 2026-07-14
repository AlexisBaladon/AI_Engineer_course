import json

from langsmith import traceable, get_current_run_tree


def decode_stream(tokens: list[str]):
    tokens = [token.replace('data: {"token": "', '{"token": "') for token in tokens]
    tokens = [token.replace('"}\n\n', '"}') for token in tokens]

    final_response = ""
    for token in tokens:
        if "[DONE]" in token:
            break

        cleaned_token = json.loads(token).get("token", "")
        final_response = final_response + cleaned_token

    additional_information = tokens[-1]
    parsed_additional_information = json.loads(additional_information)

    return {"response": final_response, "additional_information": parsed_additional_information}