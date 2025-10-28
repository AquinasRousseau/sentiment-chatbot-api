from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import os

# No load_dotenv()—Vercel uses direct env vars
llm = ChatOpenAI(api_key=os.getenv('OPENAI_API_KEY'), model="gpt-3.5-turbo", temperature=0)  # temperature=0 for consistency

prompt = PromptTemplate(
    input_variables=["text"],
    template="""Classify the sentiment of this user message as POSITIVE, NEGATIVE, or NEUTRAL. 
Output ONLY the word (all caps, no punctuation or extra text): 

Message: {text}

Sentiment:"""
)

chain = prompt | llm

def analyze_sentiment(text):
    try:
        result = chain.invoke({"text": text})
        output = result.content.strip().lower()  # Clean it
        # Parse first word (handles "Neutral." → "neutral")
        first_word = output.split()[0] if output.split() else output
        if first_word in ['positive', 'negative', 'neutral']:
            return first_word
        # Fallback: Check for common variants
        if any(word in output for word in ['pos', 'good', 'happy', 'love']):
            return 'positive'
        elif any(word in output for word in ['neg', 'bad', 'frustrated', 'hate']):
            return 'negative'
        else:
            return 'neutral'
    except Exception as e:
        print(f"Sentiment error: {e}")  # For logs
        return 'neutral'
