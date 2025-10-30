import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import logging
import re  # Explicit import for regex

load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env! Get one from platform.openai.com/api-keys and add it.")

llm = ChatOpenAI(api_key=api_key, model="gpt-4o-mini", temperature=0)

prompt = PromptTemplate(
    input_variables=["text"],
    template="""Classify the user's message into one intent: test_drive, info, support, capabilities, pricing, portfolio, general_upwork, or general.
Output ONLY the intent name (lowercase, no punctuation, no extra text or explanations). 

Examples:
Message: Test drive a Model Y?
Intent: test_drive

Message: What's the price?
Intent: info

Message: My battery died
Intent: support

Message: What kinds of chatbots do you build?
Intent: capabilities

Message: How much for a custom bot?
Intent: pricing

Message: Show me your portfolio
Intent: portfolio

Message: Can you help with my Upwork project?
Intent: general_upwork

Message: Hi there
Intent: general

Message: {text}
Intent:"""
)

chain = prompt | llm

def detect_intent(text):
    intent = 'general'  # Default
    try:
        result = chain.invoke({"text": text})
        raw_output = result.content.strip()
        logging.info(f"Raw LLM intent output for '{text}': '{raw_output}'")
        
        # Robust extraction: Look for intent via regex (case-insensitive)
        match = re.search(r'\b(test_drive|info|support|capabilities|pricing|portfolio|general_upwork|general)\b', raw_output.lower())
        if match:
            intent = match.group(1)
            logging.info(f"Regex extracted intent: '{intent}'")
        else:
            # Fallback: Keyword scan
            output_lower = raw_output.lower()
            if any(word in output_lower for word in ['test drive', 'demo', 'schedule', 'try']):
                intent = 'test_drive'
            elif any(word in output_lower for word in ['price', 'specs', 'range', 'info']):
                intent = 'info'
            elif any(word in output_lower for word in ['help', 'support', 'issue', 'problem']):
                intent = 'support'
            elif any(word in output_lower for word in ['build', 'capabilities', 'kinds', 'types']):
                intent = 'capabilities'
            elif any(word in output_lower for word in ['cost', 'price', 'much', 'quote']):
                intent = 'pricing'
            elif any(word in output_lower for word in ['portfolio', 'examples', 'work', 'demo']):
                intent = 'portfolio'
            elif any(word in output_lower for word in ['upwork', 'hire', 'project', 'job']):
                intent = 'general_upwork'
            else:
                intent = 'general'
            logging.info(f"Fallback extracted intent: '{intent}'")
        
        logging.info(f"Final intent for '{text}': '{intent}'")
        
    except Exception as e:
        logging.error(f"Intent error: {e}")
        intent = 'general'
    
    return intent

# Standalone test
if __name__ == "__main__":
    print(detect_intent("What kinds of chatbots do you build?"))  # capabilities
    print(detect_intent("Can I test drive a Tesla?"))  # test_drive
    print(detect_intent("How much?"))  # pricing
