import os
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, session
from flask_cors import CORS
from dotenv import load_dotenv
from functools import wraps
import logging

# Load env vars early
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'devtest123')
CORS(app)

# Logging setup for Vercel
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Auth decorator (simple API key check)
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.getenv('API_KEY', 'devtest123'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Import models (after env load)
from models.sentiment_model import analyze_sentiment
from models.intent_model import detect_intent
from chains.response_chain import generate_response

# Health check
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

# Demo page (HTML + JS) - Conversational chat UI
@app.route("/", methods=["GET", "POST"])
def index():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Upwork Chatbot Demo</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 20px auto; padding: 20px; background: #f5f5f5; }
            #chat-container { background: white; border-radius: 10px; height: 500px; overflow-y: auto; padding: 20px; margin-bottom: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .message { margin-bottom: 15px; padding: 10px; border-radius: 10px; max-width: 70%; word-wrap: break-word; }
            .user { background: #007bff; color: white; margin-left: auto; text-align: right; }
            .bot { background: #e9ecef; color: #333; margin-right: auto; }
            #input-container { display: flex; gap: 10px; }
            #message { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
            h1 { text-align: center; color: #333; }
            .quick-tip { text-align: center; color: #666; font-style: italic; }
            .bot strong { font-weight: bold; color: #007bff; }
            .bot em { font-style: italic; color: #28a745; }
            .bot a { color: #007bff; text-decoration: none; }
            .bot a:hover { text-decoration: underline; }
            .bot table { border-collapse: collapse; width: 100%; margin-top: 10px; }
            .bot th, .bot td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            .bot th { background: #f8f9fa; }
        </style>
    </head>
    <body>
        <h1>AI Chatbot Demo: Start Chatting!</h1>
        <p class="quick-tip">Try: "What chatbots do you build?" or "Fees too high—frustrated!"</p>
        
        <div id="chat-container"></div>
        
        <div id="input-container">
            <input type="text" id="message" placeholder="Type your message..." />
            <button onclick="sendMessage()">Send</button>
        </div>
        
        <script>
            let chatHistory = [];  
            
            const API_URL = '/analyze-chat';
            const HEADERS = { 
                'Content-Type': 'application/json', 
                'X-API-Key': 'devtest123' 
            };
            
            function addMessage(content, isUser = false) {
                const chatContainer = document.getElementById('chat-container');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
                if (isUser) {
                    messageDiv.textContent = content;
                } else {
                    messageDiv.innerHTML = content;
                }
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
                chatHistory.push({ role: isUser ? 'user' : 'bot', content });
            }
            
            async function sendMessage() {
                const input = document.getElementById('message');
                const userMessage = input.value.trim();
                if (!userMessage) return;
                
                addMessage(userMessage, true);
                input.value = '';
                
                const chatContainer = document.getElementById('chat-container');
                const thinkingDiv = document.createElement('div');
                thinkingDiv.className = 'message bot';
                thinkingDiv.textContent = 'Thinking...';
                chatContainer.appendChild(thinkingDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
                
                try {
                    const response = await fetch(API_URL, {
                        method: 'POST',
                        headers: HEADERS,
                        body: JSON.stringify({ message: userMessage })
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
                    }
                    const result = await response.json();
                    
                    chatContainer.removeChild(thinkingDiv);
                    addMessage(result.ai_response, false);
                    
                    console.log('Sentiment:', result.sentiment, 'Intent:', result.intent);
                } catch (e) {
                    chatContainer.removeChild(thinkingDiv);
                    addMessage(`Error: ${e.message}. Check console (F12).`, false);
                }
            }
            
            document.getElementById('message').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendMessage();
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

# Main endpoint
@app.route("/analyze-chat", methods=["POST"])
@require_auth
def analyze_chat():
    start_time = time.time()
    
    data = request.json
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    logger.info(f"Received message: '{user_message}'")
    
    # Session history for multi-turn context
    history = session.get('history', [])
    print(f"Loaded history length: {len(history)}")  # Debug
    history.append({'role': 'user', 'content': user_message})
    
    # Sentiment analysis
    sentiment = analyze_sentiment(user_message)
    logger.info(f"Computed sentiment: '{sentiment}'")
    
    # Intent detection
    intent = detect_intent(user_message)
    logger.info(f"Detected intent: '{intent}'")
    
    # Generate response based on intent (pass recent history for context)
    recent_history = history[-5:] if len(history) >= 5 else history
    print(f"Passing recent history length: {len(recent_history)}")  # Debug
    if intent == "capabilities":
        ai_response = """I specialize in <strong>custom chatbots</strong> tailored for Upwork clients like you! Here's what I can build:<br><br>
<ul>
<li><strong>Empathetic Support Bots</strong>: Detects frustration (e.g., "Fees too high?") and responds with apologies + fixes—perfect for <em>fintech/ecom</em> (like our live demo).</li>
<li><strong>Lead Gen Bots</strong>: For <a href="https://tesla.com" target="_blank">Tesla-style sales</a>—handles "Test drive?" with booking links + ZIP-based store finder.</li>
<li><strong>Info/Query Bots</strong>: Quick facts on products/services (e.g., "Model 3 specs?") with dynamic data pulls.</li>
<li><strong>Multi-Turn Convo Bots</strong>: Remembers context for seamless chats (e.g., "Follow up on that drive?").</li>
</ul>
Built with Python/Flask + OpenAI (<em>GPT-4o-mini for speed</em>). Scalable on Vercel/AWS. <strong>Starting at $300</strong>—let's customize for your niche! What's your project idea? 🚀"""
    elif intent == "pricing":
        ai_response = """<strong>Transparent pricing</strong> for Upwork-quality bots:<br><br>
<table>
<tr><th>Tier</th><th>Features</th><th>Price</th><th>Timeline</th></tr>
<tr><td>Basic</td><td>Rule-based intents, simple responses, Vercel deploy</td><td>$250-500</td><td>3-5 days</td></tr>
<tr><td>Pro</td><td>LLM-powered (OpenAI), sentiment/intent detection, multi-turn</td><td>$500-1k</td><td>1 week</td></tr>
<tr><td>Custom</td><td>Tesla API integration, analytics, handover + support</td><td>$1k+</td><td>2 weeks</td></tr>
</table>
Includes testing, docs, and 1-month tweaks. <em>100% satisfaction</em>—milestone payments. DM your specs for a <strong>free quote</strong>! 💰"""
    elif intent == "portfolio":
        ai_response = """<strong>Check my work</strong>:<br><br>
<ul>
<li><strong>Empathy Bot Demo</strong>: Live at <a href="[your-vercel-url]" target="_blank">your-vercel-url</a>—try "Frustrated with fees?" for real-time magic. GitHub: <a href="https://github.com/yourusername/empathetic-bot" target="_blank">github.com/yourusername/empathetic-bot</a>.</li>
<li><strong>Tesla Lead Bot</strong>: Simulated test drive scheduler (code snippet on request).</li>
<li><strong>Upwork Wins</strong>: 5* reviews for 3 bots (e.g., ecom query handler—boosted conversions <em>20%</em>).</li>
</ul>
Full portfolio: <a href="[your-upwork-profile]" target="_blank">your-upwork-profile</a>. Let's build yours next—what's the vision? 📁"""
    elif intent == "test_drive":
        ai_response = f'<em>Excited for your test drive</em>! Based on your <strong>{sentiment}</strong> vibe, let\'s get you behind the wheel. Enter your ZIP: <a href="https://www.tesla.com/drive" target="_blank">Schedule</a>. Pro tip: Ask about FSD upgrades! 🏎️'
    elif intent == "info":
        ai_response = "<strong>Happy to dive into Tesla details</strong>! For Model 3: <em>358 mi range</em>, <strong>$40k starting</strong>. More at <a href='https://tesla.com/model3' target='_blank'>tesla.com/model3</a>. What specifics?"
    elif intent == "support":
        ai_response = f"<em>I'm here to help</em>—sorry if you're <strong>{sentiment}</strong>! What's the issue? Quick fixes: Check app updates or reset via settings. Need more? 🔧"
    else:  # general or upwork fallback
        ai_response = generate_response(user_message, sentiment, recent_history)
    
    # Append bot response to history
    history.append({'role': 'bot', 'content': ai_response})
    session['history'] = history[-20:]  # Cap at 20 for token limits
    print(f"Saved history length: {len(session['history'])}")  # Debug
    
    analysis_time = round((time.time() - start_time) * 1000, 2)
    
    logger.info(f"Generated response preview: '{ai_response[:50]}...' | Time: {analysis_time}ms")
    
    return jsonify({
        "sentiment": sentiment,
        "intent": intent,
        "ai_response": ai_response,
        "analysis_time": f"{analysis_time}ms"
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
