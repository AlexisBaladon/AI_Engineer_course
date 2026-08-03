from openai import OpenAI
from langchain_core.runnables import Runnable
from langsmith import traceable


QUERY_FILTER_CACHE = {}


class QueryFilter(Runnable[str, dict]):
    """
    LangChain Runnable wrapper around the OpenAI Moderation API.
    """

    def __init__(
        self,
        client: OpenAI | None = None,
        model: str = "omni-moderation-latest",
    ):
        self.client = client or OpenAI()
        self.model = model

    def invoke(self, input: str, config=None) -> dict:
        response = self.client.moderations.create(
            model=self.model,
            input=input,
        )

        result = response.results[0]

        return {
            "is_inappropriate": result.flagged,
            "categories": result.categories.model_dump(),
            "category_scores": result.category_scores.model_dump(),
        }


@traceable(type="llm", name="Query filter")
def filter_query(query: str, llm: Runnable):
    cache_key = query
    cached = QUERY_FILTER_CACHE.get(cache_key)

    if cached is not None:
        return cached

    result = llm.invoke(query)

    QUERY_FILTER_CACHE[cache_key] = result

    return result