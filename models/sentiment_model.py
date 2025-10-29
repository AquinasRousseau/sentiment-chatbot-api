from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import os
import re  # New: For robust extraction

# No load_dotenv()—Vercel uses direct env vars
llm = ChatOpenAI(api_key=os.getenv('OPENAI_API_KEY'), model="gpt-4o-mini", temperature=0)

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
    try:
        result = chain.invoke({"text": text})
        raw_output = result.content.strip()  # Add this line
        print(f"Raw LLM output for '{text}': '{raw_output}'")  # Debug print
        
        output = raw_output.lower()
        # ... rest of your code
   
        if match:
            return match.group(1)
        
        # Expanded fallback: Scan whole output for keywords
        output_lower = raw_output.lower()
        if any(word in output_lower for word in ['love', 'great', 'awesome', 'happy', 'pos']):
            return 'positive'
        elif any(word in output_lower for word in ['hate', 'bad', 'frustrated', 'angry', 'neg', 'issue', 'problem', 'confusing']):
            return 'negative'
        else:
            return 'neutral'  # Safe default
    except Exception as e:
        print(f"Sentiment error: {e}")  # For logs
        return 'neutral'


