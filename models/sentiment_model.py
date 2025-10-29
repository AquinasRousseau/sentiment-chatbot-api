import os
import time  # For rate-limit sleep
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import re
import logging  # Structured logs for Vercel

load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env! Get one from platform.openai.com/api-keys and add it.")

llm = ChatOpenAI(api_key=api_key, model="gpt-4o-mini", temperature=0)

prompt = PromptTemplate(
    input_variables=["text"],
    template="""Classify the sentiment of this user message as POSITIVE, NEGATIVE, or NEUTRAL. 
Output ONLY the word (all caps, no punctuation, no extra text or explanations). 

Examples:
Message: I love this app!
Sentiment: POSITIVE

Message: How do I reset my password?
Sentiment: NEUTRAL

Message: The fees are too high and I'm frustrated!
Sentiment: NEGATIVE

Message: {text}
Sentiment:"""
)

chain = prompt | llm

def analyze_sentiment(text):
    sentiment = 'neutral'  # Default—always set
    match = None  # Declare early: Fixes "not defined" scope error
    try:
        result = chain.invoke({"text": text})
        raw_output = result.content.strip()
        logging.info(f"Raw LLM output for '{text}': '{raw_output}'")
        
        # Robust extraction: Regex for sentiment (handles punctuation/trailing junk)
        match = re.search(r'\b(positive|negative|neutral)[.!?]?\b', raw_output.lower())
        if match:
            sentiment = match.group(1).strip(' .!?,')
            logging.info(f"Regex extracted: '{sentiment}'")
        else:
            # Fallback: Keyword scan if regex misses (e.g., verbose LLM output)
            output_lower = raw_output.lower()
            if any(word in output_lower for word in ['love', 'great', 'awesome', 'happy', 'pos']):
                sentiment = 'positive'
            elif any(word in output_lower for word in ['hate', 'bad', 'frustrated', 'angry', 'neg', 'issue', 'problem', 'confusing']):
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            logging.info(f"Fallback extracted: '{sentiment}'")
        
        logging.info(f"Final sentiment for '{text}': '{sentiment}'")
        
    except Exception as e:
        logging.error(f"Sentiment error: {e}")
        if "429" in str(e):  # Rate limit
            logging.warning("Rate limited—sleeping 30s")
            time.sleep(30)
        sentiment = 'neutral'  # Safe default
    
    return sentiment

# Standalone test (local: python models/sentiment_model.py)
if __name__ == "__main__":
    print(analyze_sentiment("Love the new features!"))  # positive
    print(analyze_sentiment("How do I reset password?"))  # neutral
    print(analyze_sentiment("Fees too high—frustrated!"))  # negative


