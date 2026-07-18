from flask import Flask, jsonify, request, Response, make_response, stream_with_context
from flask_cors import CORS
from langsmith import traceable
from openai import OpenAI
from langchain_openai import ChatOpenAI
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from constants import (
    HOST,
    PORT,
    DEBUG,
    ADMIN_USER_USERNAME,
    ADMIN_USER_PASSWORD,
    ENCRYPTION_SECRET_KEY,
    FRONTEND_ORIGIN,
    USER_ROLE,
    ADMIN_ROLE,
    CHUNKED_DATA_PATH,
    IMAGES_PATH,
)
from authentication.authentication_handler import (
    create_token,
    get_current_user,
)
from orchestation.observability.langsmith_tracing import (
    decode_stream, 
    get_current_run_tree
)
from orchestation.prompts_handler import (
    fill_user_prompt,
    system_prompt,
)
from orchestation.graph_handler import (
    RAGState,
    build_graph,
)
from retrieval.retrieval_handler import (
    load_chunks,
    build_bm25_index,
    build_faiss_index,
    search,
)
from ranking.reranking_handler import (
    rerank_chunks,
)
from judge.reasoning_handler import (
    judge_context,
    rewrite_query,
)
from agent.agent_handler import (
    build_messages,
    generate_and_trace,
    stream_response,
)

import json

app = Flask(__name__)

print(f"Server expects to recieve API calls from: {FRONTEND_ORIGIN}")

CORS(app, origins=[FRONTEND_ORIGIN], supports_credentials=True)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
)

openai_client = OpenAI()
chunks = load_chunks(CHUNKED_DATA_PATH, IMAGES_PATH)
bm25 = build_bm25_index(chunks)
faiss_index = build_faiss_index(chunks)
llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
    streaming=True,
)


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if (
        username == ADMIN_USER_USERNAME
        and password == ADMIN_USER_PASSWORD
    ):
        token = create_token(username, encryption_secret_key=ENCRYPTION_SECRET_KEY)

        resp = make_response(
            jsonify({"message": "Login successful"})
        )

        resp.set_cookie(
            "auth_token",
            token,
            httponly=True, # HttpOnly cookie prevents JS access (important security)
            secure=DEBUG,  # TODO: set True in HTTPS production
            samesite="Lax",
        )

        return resp

    return jsonify(
        {"message": "Invalid credentials"}
    ), 401


@app.route("/logout", methods=["POST"])
def logout():
    resp = make_response(
        jsonify({"message": "Logged out"})
    )

    resp.delete_cookie("auth_token")

    return resp


@app.route("/auth/status", methods=["GET"])
def auth_status():
    user = get_current_user(request.cookies, encryption_secret_key=ENCRYPTION_SECRET_KEY)

    if user is None:
        return jsonify({
            "authenticated": False,
        }), 401

    return jsonify({
        "authenticated": True,
        "username": user,
    }), 200


def _get_last_message(user_conversation: list[dict]):
    return next(
        (
            message["content"]
            for message in reversed(user_conversation)
            if message["role"] == "user"
        ),
        None,
    )


def retrieve_node(state: RAGState):
    top_k = 5

    query = state.get("query")

    if query is None:
        query = _get_last_message(state["user_conversation"])

    retrieved_chunks = search(
        query=query,
        bm25=bm25,
        faiss_index=faiss_index,
        openai_client=openai_client,
        chunks=chunks,
        top_k=top_k,
    )

    return {
        "query": query,
        "retrieved_chunks": retrieved_chunks,
    }


def rank_node(state: RAGState):
    top_k = 3

    reranked_results = rerank_chunks(
        state["query"],
        state["retrieved_chunks"],
        openai_client,
    )

    top_results = reranked_results[:top_k]

    return {
        "retrieved_chunks": top_results,
    }


def build_prompt_node(state: RAGState):
    role = state["role"]
    chunks = state["retrieved_chunks"]
    documents =  [chunk["chunk_text"] for chunk in chunks]
    images = [chunk["images"] for chunk in chunks]
    urls = [chunk["url"] for chunk in chunks]
    rag_prompt = fill_user_prompt(state["query"], documents, urls, images, role)
    
    conversation_for_generation = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]
    conversation_for_generation.extend(state["user_conversation"][:-1])
    conversation_for_generation.append(
        {
            "role": "user",
            "content": rag_prompt,
        }
    )

    return {"conversation_for_generation": conversation_for_generation}




def judge_context_node(state: RAGState):
    if state["iteration"] >= state["max_iterations"]:
        return {
            "enough_context": True,
        }

    result = judge_context(
        state["query"],
        state["retrieved_chunks"],
        openai_client,
    )

    return {
        "enough_context": result["enough_context"],
    }


def rewrite_query_node(state: RAGState):
    result = rewrite_query(
        state["query"], 
        state["retrieved_chunks"], 
        openai_client
    )

    rewritten_query = result["query"]

    return {
        "query": rewritten_query,
        "iteration": state["iteration"] + 1,
        "query_history": (
            state["query_history"]
            + [rewritten_query]
        ),
    }


def generate_node(state: RAGState):
    raw_messages = state["conversation_for_generation"]
    stream = state.get("stream", False)

    if not raw_messages:
        return jsonify({
            "error": "messages is required"
        }), 400

    try:
        messages = build_messages(raw_messages)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    if stream:
        answer_stream = stream_response(llm, messages)

        return {
            "answer": None,
            "answer_stream": answer_stream
        }
    result, _ = (generate_and_trace(llm, messages))

    return {
        "answer": result,
        "answer_stream": None,
    }


rag_graph = build_graph(
    retrieve_node,
    rank_node,
    judge_context_node,
    rewrite_query_node,
    build_prompt_node,
    generate_node,
)


@traceable(
    run_type="llm",
    name="Final response",
    reduce_fn=decode_stream,
)
def generate_chunks(answer_stream, additional_information: dict):
    for chunk in answer_stream:
        yield chunk

    yield json.dumps(additional_information)


@traceable(name="Main Chain")
def answer_query_and_trace(messages: list[str], role="user", stream: bool = False):
    tracing_tree = get_current_run_tree()
    tracing_headers = tracing_tree.to_headers()

    result = rag_graph.invoke({
        "user_conversation": messages,
        "stream": stream,
        "role": role,
        "iteration": 0,
        "max_iterations": 0,
        "query_history": [],
    })

    if stream:
        additional_information = {
            "system_prompt": system_prompt,
            "query": result["query"],
            "query_history": result.get("query_history", [result["query"]]),
            "iterations": result.get("iteration", 0),
            "role": result["role"],
            "retrieval_information": [
                {
                    "chunk_text": chunk["chunk_text"],
                    "lexical_score": chunk["lexical_score"],
                    "semantic_score": chunk["semantic_score"],
                }
                for chunk in result["retrieved_chunks"]
            ],
        }
        result["answer_stream"] = generate_chunks(
            result["answer_stream"], 
            additional_information,
            langsmith_extra={
                "parent": tracing_headers,
        },)
        return result, 200
    return result, 200


@app.route("/chat", methods=["POST"])
def run_chain():
    body = request.get_json()

    messages = body.get("messages", [])
    stream = body.get("stream", False)
    user = get_current_user(request.cookies, encryption_secret_key=ENCRYPTION_SECRET_KEY)
    role = ADMIN_ROLE if user is not None else USER_ROLE

    result, status_code = answer_query_and_trace(messages, role, stream=stream)

    if stream:
        return Response(
            stream_with_context(result["answer_stream"]),
            mimetype="text/event-stream",
        )

    result, status_code = answer_query_and_trace(messages, role, stream=False)
    return jsonify(result), status_code


@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG,
    )