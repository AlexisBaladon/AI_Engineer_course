import csv
import json
import time
import requests
import subprocess
from datetime import datetime, timezone


MAIN_CHAIN_URL = "http://localhost:1232/run_chain"

INPUT_CSV = "test_dataset.csv"
OUTPUT_JSON = "llm_results.json"


def get_git_commit():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True
        ).strip()
    except Exception:
        return None
    

def ask_llm(question):
    payload = {
        "messages": [
            {
                "role": "user",
                "content": question,
            }
        ],
        "stream": True,
    }

    start_time = time.perf_counter()

    response = requests.post(
        MAIN_CHAIN_URL,
        json=payload,
        stream=True,
    )

    response.raise_for_status()

    full_answer = []
    metadata = None
    first_token_time = None
    done_received = False

    for raw_line in response.iter_lines(decode_unicode=True):
        if not raw_line:
            continue

        payload = raw_line

        if raw_line.startswith("data: "):
            payload = raw_line[6:].strip()

            if "[DONE]" in payload:
                done_received = True
                continue

        try:
            obj = json.loads(payload)
        except Exception as e:
            print(e)
            continue

        # Before DONE -> streamed tokens
        if not done_received:
            token = obj.get("token", "")

            if token:
                if first_token_time is None:
                    first_token_time = (
                        time.perf_counter() - start_time
                    )

                full_answer.append(token)

        # After DONE -> metadata
        else:
            metadata = obj

    return {
        "query": question,
        "answer": "".join(full_answer),
        "time_to_first_token": first_token_time,
        "metadata": metadata,
    }


def main():
    results = []
    last_commit = get_git_commit()
    experiment_date = datetime.now(timezone.utc).isoformat()

    with open(INPUT_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        idx = 0

        for row in reader:
            idx += 1

            if idx > 1:
                continue

            question = row["pregunta"]
            print(f"Asking: {question}")
            run = ask_llm(question)
            metadata = run["metadata"] or {}

            result = {
                "query": metadata.get("query", question),
                "answer": run["answer"],
                "time_to_first_token": run["time_to_first_token"],
                "system_prompt": metadata.get("system_prompt"),
                "retrieved_documents": metadata.get("retrieval_information", []),
                "last_commit": last_commit,
                "experiment_date": experiment_date,
            }

            results.append(result)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(
            results,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Saved {len(results)} runs.")


if __name__ == "__main__":
    main()