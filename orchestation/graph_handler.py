from typing import TypedDict

from langgraph.graph import StateGraph, START, END


class RAGState(TypedDict):
    query: str
    user_conversation: list[dict]
    role: str
    stream: bool

    retrieved_chunks: list

    conversation_for_generation: list[dict]
    
    answer: dict
    answer_stream: object


def build_graph(
    retrieve_node,
    rank_node,
    build_prompt_node,
    generate_node,
):
    graph_builder = StateGraph(RAGState)
    graph_builder.add_node("retrieve", retrieve_node)
    graph_builder.add_node("rank", rank_node)
    graph_builder.add_node("build_prompt", build_prompt_node)
    graph_builder.add_node("generate", generate_node)
    graph_builder.add_edge(START, "retrieve")
    graph_builder.add_edge("retrieve", "rank")
    graph_builder.add_edge("rank", "build_prompt")
    graph_builder.add_edge("build_prompt", "generate")
    graph_builder.add_edge("generate", END)
    return graph_builder.compile()