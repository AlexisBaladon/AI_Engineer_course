import json
import statistics
from collections import Counter
from datetime import datetime

INPUT_FILE = "llm_metrics.json"
OUTPUT_FILE = "report.md"


def mean(values):
    values = [v for v in values if v is not None]
    if not values:
        return None
    return statistics.mean(values)


def fmt(value, digits=2):
    if value is None:
        return "-"
    return f"{value:.{digits}f}"


if __name__ == "__main__":
    with open(INPUT_FILE, encoding="utf-8") as f:
        runs = json.load(f)

    # -------------------------------
    # Metadata
    # -------------------------------

    metadata = runs[0]

    experiment_date = metadata.get("experiment_date", "-")
    commit = metadata.get("last_commit", "-")
    retrieval_method = metadata.get("retrieval_method", "Hybrid Search")
    llm = metadata.get("llm_model", "gpt-4.1-mini")
    reranking_model = metadata.get("reranking_model", "gpt-4.1-mini")
    embedding = metadata.get("embedding_model", "text-embedding-3-small")

    # -------------------------------
    # Metrics
    # -------------------------------

    ttft = [
        run["time_to_first_token"]
        for run in runs
    ]


    faithfulness_scores = []

    relevance_scores = []

    for run in runs:
        evaluation = run.get("evaluation", {})
        faithfulness = evaluation.get("faithfulness", {})
        relevance = evaluation.get("document_relevance", {})

        if faithfulness.get("score") is not None:
            faithfulness_scores.append(faithfulness["score"])

        precision = (
            sum(
                evaluation["label"] == "relevant"
                for evaluation in run["evaluation"]["document_relevance"]["documents"]
            )
            / len(run["evaluation"]["document_relevance"]["documents"])
    )
        relevance_scores.append(precision)

    faithfulness_labels = Counter(
        run["evaluation"]["faithfulness"]["label"]
        for run in runs
    )


    # -------------------------------
    # Worst queries
    # -------------------------------

    worst_queries = sorted(
        runs,
        key=lambda x:
        x["evaluation"]["faithfulness"]["score"]
    )[:10]

    # -------------------------------
    # Best queries
    # -------------------------------

    best_queries = sorted(
        runs,
        key=lambda x:
        x["evaluation"]["faithfulness"]["score"],
        reverse=True
    )[:10]

    # -------------------------------
    # Markdown
    # -------------------------------

    markdown = f"""# 🧠 Nau64 RAG Evaluation Report

    > Automatically generated benchmark report.

    ---

    # 📋 Experiment Information

    | Property | Value |
    |-----------|------:|
    | Date | {experiment_date} |
    | Git Commit | `{commit}` |
    | Embedding Model | {embedding} |
    | Retrieval Method | {retrieval_method} |
    | Re-ranking Model | {reranking_model} |
    | LLM | {llm} |
    | Number of Questions | {len(runs)} |

    ---

    # 📊 Overall Metrics

    | Metric | Value |
    |---------|------:|
    | Average Time to First Token | **{fmt(mean(ttft))} s** |
    | Average Faithfulness | **{fmt(mean(faithfulness_scores),3)}** |
    | Precision@k | **{fmt(mean(relevance_scores),3)}** |

    ---

    # ✅ Faithfulness Distribution

    | Label | Count |
    |--------|------:|
    """

    for label, count in faithfulness_labels.items():
        markdown += f"| {label} | {count} |\n"

    markdown += """

    ---

    # ⚡ Latency

    | Metric | Seconds |
    |---------|--------:|
    """

    markdown += f"| Fastest TTFT | {fmt(min(ttft))} |\n"
    markdown += f"| Slowest TTFT | {fmt(max(ttft))} |\n"


    markdown += f"""

    ---

    # 📈 Executive Summary

    This benchmark evaluated **{len(runs)}** user questions against the
    latest version of the Nau64 RAG system.

    ## Highlights

    - Average Time to First Token: **{fmt(mean(ttft))} seconds**
    - Average Faithfulness: **{fmt(mean(faithfulness_scores),3)}**
    - Average Precision@k: **{fmt(mean(relevance_scores),3)}**

    The benchmark was generated automatically from commit `{commit}` on
    {experiment_date}.
    """

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as f:
        f.write(markdown)

    print(f"Report written to {OUTPUT_FILE}")