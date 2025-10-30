import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import logging

load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env!")

llm = ChatOpenAI(api_key=api_key, model="gpt-4o-mini", temperature=0.3)

def summarize_history(history: list) -> str:
    """Quick summary of last 3 turns (user/bot pairs) to avoid token bloat."""
    if not history:
        return "No prior context."
    recent = history[-6:]  # Last up to 3 turns
    summary = []
    for i in range(0, len(recent), 2):
        if i + 1 < len(recent) and 'content' in recent[i] and 'content' in recent[i+1]:
            u_content = recent[i]['content'][:50] + '...' if len(recent[i]['content']) > 50 else recent[i]['content']
            b_content = recent[i+1]['content'][:50] + '...' if len(recent[i+1]['content']) > 50 else recent[i+1]['content']
            summary.append(f"User: {u_content} | Bot: {b_content}")
        elif i < len(recent) and 'content' in recent[i]:
            summary.append(f"Latest User: {recent[i]['content'][:50]}...")
    return '\n'.join(summary) + '\nLatest: ' if summary else 'No prior context.\nLatest: '

prompt = PromptTemplate(
    input_variables=["history_summary", "user_message", "sentiment"],
    template="""You are a helpful, professional chatbot for a developer showcasing Upwork skills. 

Conversation history (for context): {history_summary}

User's latest message: {user_message}
User's sentiment: {sentiment}

Respond empathetically and concisely (under 150 words). If general, tie back to chatbot building/sales (e.g., "Sounds frustrating—I've built bots to handle that!"). End with a question to continue the convo. Keep engaging and promotional where natural."""
)

chain = prompt | llm

def generate_response(user_message: str, sentiment: str, history: list = []) -> str:
    try:
        history_summary = summarize_history(history)
        logging.info(f"History summary: {history_summary[:100]}...")  # Debug log
        result = chain.invoke({
            "history_summary": history_summary,
            "user_message": user_message,
            "sentiment": sentiment
        })
        response = result.content.strip()
        logging.info(f"Generated response with history: '{response[:50]}...'")
        return response
    except Exception as e:
        logging.error(f"Response generation error: {e}")
        # Fallback: Simple empathetic reply
        return f"I'm sorry if you're feeling {sentiment}—let's chat about custom chatbots! What feature interests you most?"
