import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import re  # For robust extraction

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
    sentiment = 'neutral'  # Default outside try for safety
    try:
        result = chain.invoke({"text": text})
        raw_output = result.content.strip()
        print(f"Raw LLM output for '{text}': '{raw_output}'")  # Your existing debug
        
        # Robust extraction: Look for the sentiment word via regex (case-insensitive)
        match = re.search(r'\b(positive|negative|neutral)\b', raw_output.lower())
        if match:
            sentiment = match.group(1)
            print(f"Regex extracted: '{sentiment}'")  # New: Log the win
        
        # Expanded fallback: Scan whole output for keywords (only if regex misses)
        else:
            output_lower = raw_output.lower()
            if any(word in output_lower for word in ['love', 'great', 'awesome', 'happy', 'pos']):
                sentiment = 'positive'
            elif any(word in output_lower for word in ['hate', 'bad', 'frustrated', 'angry', 'neg', 'issue', 'problem', 'confusing']):
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            print(f"Fallback extracted: '{sentiment}'")  # Log fallback use
        
        print(f"Final sentiment for '{text}': '{sentiment}'")  # Overall log
        
    except Exception as e:
        print(f"Sentiment error: {e}")
        sentiment = 'neutral'  # Ensure it's set even on error
    
    return sentiment

# Standalone test
if __name__ == "__main__":
    print(analyze_sentiment("Love the new features!"))  # positive
    print(analyze_sentiment("How do I reset password?"))  # neutral
    print(analyze_sentiment("Fees too high—frustrated!"))  # negative
