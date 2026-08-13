import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

# Use ChatOpenAI but point it to OpenRouter's endpoint
llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
    model_name=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),  # Or any OpenRouter model
)

# The rest is exactly the same as your original code!
prompt = ChatPromptTemplate.from_template("Tell me a joke about {topic} in {style} style.")
output_parser = StrOutputParser()
chain = prompt | llm | output_parser
user_input = input('You: ')
response = chain.invoke({"topic": user_input,"style":"dark humor"})
print(f"AI: {response}")