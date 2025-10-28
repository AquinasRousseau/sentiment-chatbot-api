from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()
llm = ChatOpenAI(api_key=os.getenv('OPENAI_API_KEY'), model="gpt-3.5-turbo")

prompt = PromptTemplate(
    input_variables=["text"],
    template="Analyze the sentiment of this message: '{text}'. Respond with only one word: 'positive', 'negative', or 'neutral'."
)

chain = prompt | llm

def analyze_sentiment(text):
    try:
        result = chain.invoke({"text": text})
        sentiment = result.content.strip().lower()
        if sentiment not in ['positive', 'negative', 'neutral']:
            sentiment = 'neutral'  # Fallback
        return sentiment
    except Exception:
        return 'neutral'  # Graceful error handling
