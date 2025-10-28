import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env! Get one from platform.openai.com/api-keys and add it.")
os.environ["OPENAI_API_KEY"] = api_key

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)  # Balanced creativity

# Dynamic prompt based on sentiment
prompt_template = """
You are an empathetic customer support bot for a fintech app.
User message: {user_message}
Sentiment analysis: {sentiment}

Respond helpfully and empathetically:
- If POSITIVE: Be enthusiastic and upsell a feature.
- If NEUTRAL: Provide clear info and ask a follow-up.
- If NEGATIVE: Apologize, resolve the issue, and offer next steps.
Keep response under 100 words.
"""

prompt = PromptTemplate(input_variables=["user_message", "sentiment"], template=prompt_template)
chain = LLMChain(llm=llm, prompt=prompt)

def generate_response(user_message: str, sentiment: str) -> str:
    return chain.run(user_message=user_message, sentiment=sentiment)

# Standalone test
if __name__ == "__main__":
    print(generate_response("Billing is confusing!", "NEGATIVE"))
    print(generate_response("How do I reset my password?", "NEUTRAL"))
    print(generate_response("Love the new features!", "POSITIVE"))
