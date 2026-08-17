import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
load_dotenv()

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.utils.uuid import uuid7
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import BaseModel

import tools
from config import SYSTEM_PROMPT


class Answer(BaseModel):
    summary: str
    confidence: float


model = ChatOpenAI(
    model_name="gpt-3.5-turbo",
    openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    
)
agent = create_agent(
    model=model,
    tools=tools.ALL_TOOLS,
    system_prompt=SYSTEM_PROMPT,
    # response_format=Answer,
    checkpointer=InMemorySaver(),
    middleware=[
        SummarizationMiddleware(
            model=model,
            max_summary_tokens=100,
            trigger_token_threshold=10000,
        )
    ],
)

config = {"configurable": {"thread_id": str(uuid7())}}
messages = []
while True:
    q = input("\nYou: ")
    if q.lower() == "exit":
        break

    messages.append({"role": "user", "content": q})

    response = agent.invoke(
        {"messages": [{"role": "user", "content": q}]}, config=config
    )

    assistant_message = response["messages"][-1].content

    messages.append({"role": "assistant", "content": assistant_message})
    print(f"Assistant: {assistant_message}")

# inputs = {"messages": [{"role": "user", "content": "Who is Reyan?"}]}

# for chunk in agent.stream(inputs,stream_mode='updates'):
#     print(chunk)

# self.documents = [
#             "Paris is the capital of France. It's known for the Eiffel Tower.",
#             "London is the capital of the United Kingdom. It has Big Ben.",
#             "Tokyo is the capital of Japan. It's famous for sushi.",
#         ]
