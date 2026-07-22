from typing import TypedDict

from langgraph.graph import (
    StateGraph,
    START,
    END,
)


class RAGState(TypedDict):
    # Filtering
    is_inappropriate: bool

    # Retrieval
    query: str
    retrieved_chunks: list

    # Conversation
    user_conversation: list[dict]
    conversation_for_generation: list[dict]

    # Generation
    stream: bool
    answer_stream: object
    answer: dict

    # Authentication
    role: str

    # Iterative retrieval
    query_history: list[str]
    iteration: int
    max_iterations: int

    enough_context: bool

    tracing_headers: dict | None


def route_filtered_queries(state: RAGState):
    """
    Determines whether the graph should continue
    or abort the RAG process.
    """

    if state["is_inappropriate"]:
        return "end"

    return "retrieve"


def route_after_judge(state: RAGState):
    """
    Determines whether the graph should continue
    with generation or perform another retrieval cycle.
    """

    if state["enough_context"]:
        return "build_prompt"

    if state["iteration"] >= state["max_iterations"]:
        return "build_prompt"

    return "rewrite_query"


def build_graph(
    filter_node,
    retrieve_node,
    rank_node,
    judge_context_node,
    rewrite_query_node,
    build_prompt_node,
    generate_node,
):
    graph_builder = StateGraph(RAGState)

    graph_builder.add_node(
        "filter",
        filter_node,
    )

    graph_builder.add_node(
        "retrieve",
        retrieve_node,
    )

    graph_builder.add_node(
        "rank",
        rank_node,
    )

    graph_builder.add_node(
        "judge_context",
        judge_context_node,
    )

    graph_builder.add_node(
        "rewrite_query",
        rewrite_query_node,
    )

    graph_builder.add_node(
        "build_prompt",
        build_prompt_node,
    )

    graph_builder.add_node(
        "generate",
        generate_node,
    )

    graph_builder.add_edge(
        START,
        "filter",
    )

    graph_builder.add_conditional_edges(
        "filter",
        route_filtered_queries,
        {
            "retrieve": "retrieve",
            "end": END,
        },
    )

    graph_builder.add_edge(
        "retrieve",
        "rank",
    )

    graph_builder.add_edge(
        "rank",
        "judge_context",
    )

    graph_builder.add_conditional_edges(
        "judge_context",
        route_after_judge,
        {
            "build_prompt": "build_prompt",
            "rewrite_query": "rewrite_query",
        },
    )

    graph_builder.add_edge(
        "rewrite_query",
        "retrieve",
    )

    graph_builder.add_edge(
        "build_prompt",
        "generate",
    )

    graph_builder.add_edge(
        "generate",
        END,
    )

    return graph_builder.compile()