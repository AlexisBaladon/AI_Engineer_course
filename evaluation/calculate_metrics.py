import json

from phoenix.evals import LLM
from phoenix.evals.metrics import (
    FaithfulnessEvaluator,
    DocumentRelevanceEvaluator,
)
from dotenv import load_dotenv

load_dotenv()


llm = LLM(
    provider="openai",
    model="gpt-4.1-mini",
)

faithfulness_evaluator = FaithfulnessEvaluator(llm=llm)
document_relevance_evaluator = DocumentRelevanceEvaluator(llm=llm)

INPUT_FILE = "llm_outputs.json"
OUTPUT_FILE = "llm_metrics.json"
def build_context(retrieved_documents):
    return "\n\n".join(
        document["chunk_text"]
        for document in retrieved_documents
    )


def evaluate_faithfulness(query, answer, context):
    scores = faithfulness_evaluator.evaluate(
        {
            "input": query,
            "output": answer,
            "context": context,
        }
    )

    score = scores[0]

    return {
        "label": score.label,
        "score": score.score,
    }


def evaluate_document_relevance(query, retrieved_documents):
    evaluations = []

    for document in retrieved_documents:

        scores = document_relevance_evaluator.evaluate(
            {
                "input": query,
                "document_text": document["chunk_text"],
            }
        )

        score = scores[0]

        evaluations.append(
            {
                "chunk_text": document["chunk_text"],
                "label": score.label,
                "score": score.score,
            }
        )

    average_score = (
        sum(
            evaluation["score"]
            for evaluation in evaluations
        )
        / len(evaluations)
        if evaluations
        else None
    )

    return {
        "average_score": average_score,
        "documents": evaluations,
    }


if __name__ == "__main__":
    with open(INPUT_FILE, encoding="utf-8") as f:
        runs = json.load(f)

    new_runs = []

    for i, run in enumerate(runs, start=1):
        print(f"Evaluating {i}/{len(runs)}")
        query = run["query"]
        answer = run["answer"]

        retrieved_documents = run.get("retrieved_documents", [])
        context = build_context(retrieved_documents)
        faithfulness = evaluate_faithfulness(query, answer, context)
        relevance = evaluate_document_relevance(query, retrieved_documents)
        run["evaluation"] = {
            "faithfulness": faithfulness,
            "document_relevance": relevance,
        }

        new_runs.append(run)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(new_runs, f, ensure_ascii=False, indent=2)

    print(f"Saved evaluated dataset to {OUTPUT_FILE}")