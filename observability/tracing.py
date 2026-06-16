from arize.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor
from langchain_core.messages import HumanMessage
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

from constants import ARIZE_API_KEY, ARIZE_SPACE_ID, ARIZE_PROJECT_NAME


tracer_provider = register(
    space_id = ARIZE_SPACE_ID,
    api_key = ARIZE_API_KEY,
    project_name = ARIZE_PROJECT_NAME, 
)

LangChainInstrumentor().instrument(tracer_provider=tracer_provider)


if __name__ == "__main__":
    responses = ["Hello, I am a dummy AI!", "What else do you need help with?"]
    fake_model = GenericFakeChatModel(messages=iter(responses))
    response = fake_model.invoke([HumanMessage(content="Hi!")])
