def get_additional_information(state: dict, system_prompt: str):
    return {
        "system_prompt": system_prompt,
        "query": state["query"],
        "query_history": state.get("query_history", [state["query"]]),
        "iterations": state.get("iteration", 0),
        "role": state["role"],
        "retrieval_information": [
            {
                "chunk_text": chunk["chunk_text"],
                "lexical_score": chunk["lexical_score"],
                "semantic_score": chunk["semantic_score"],
            }
            for chunk in state.get("retrieved_chunks", []) 
        ],
        "is_inappropriate": state["is_inappropriate"],
        "user_id": state["user_id"],
    }