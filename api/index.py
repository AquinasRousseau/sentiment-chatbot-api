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
        ai_response = """I specialize in <strong>custom chatbots</strong> as a Upwork freelancer! Here's what I build for clients like you:<br><br>
<ul>
<li><strong>Empathetic Support Bots</strong>: Detects frustration (e.g., "Fees too high?") and responds with fixes—perfect for <em>ecom/fintech</em> (live demo right here!).</li>
<li><strong>Lead Gen Bots</strong>: Handles "Demo a bot?" with booking links + quick needs assessment.</li>
<li><strong>Info/Query Bots</strong>: Pulls dynamic facts on your services/products.</li>
<li><strong>Multi-Turn Convo Bots</strong>: Remembers context for seamless client chats.</li>
</ul>
Built with Python/Flask + OpenAI (fast & scalable on Vercel). <strong>Starting at $300</strong>—let's tailor one for your business! What's your main use case? 🚀"""
    elif intent == "pricing":
        ai_response = """<strong>Upwork-friendly pricing</strong> for pro bots:<br><br>
<table>
<tr><th>Tier</th><th>Features</th><th>Price</th><th>Timeline</th></tr>
<tr><td>Basic</td><td>Rule-based intents, simple UI, Vercel deploy</td><td>$250-500</td><td>3-5 days</td></tr>
<tr><td>Pro</td><td>AI-powered (sentiment/intent), multi-turn memory</td><td>$500-1k</td><td>1 week</td></tr>
<tr><td>Custom</td><td>Your API integrations, analytics, full handover</td><td>$1k+</td><td>2 weeks</td></tr>
</table>
Milestone payments, 1-month support included. <em>5* reviews on Upwork</em>—DM for a <strong>free audit</strong> of your needs! 💰"""
    elif intent == "portfolio":
        ai_response = """<strong>My Upwork portfolio highlights</strong>:<br><br>
<ul>
<li><strong>Empathy Bot Demo</strong>: Live at <a href="[your-vercel-url]" target="_blank">your-vercel-url</a>—test "Frustrated with support?" for real magic. GitHub: <a href="https://github.com/AquinasRousseau/sentiment-chatbot-api" target="_blank">github.com/AquinasRousseau/sentiment-chatbot-api</a>.</li>
<li><strong>Lead Gen Bot</strong>: Boosted client conversions 20%—code on request.</li>
<li><strong>Client Wins</strong>: 3 bots for ecom/support, all 5* rated.</li>
</ul>
Full profile: <a href="https://upwork.com/freelancers/~yourprofile" target="_blank">upwork.com/freelancers/~AquinasRousseau</a>. Ready to build yours? Share your project vibe! 📁"""
    elif intent == "test_drive":
        ai_response = f'<em>Love demo requests</em>—based on your <strong>{sentiment}</strong> energy, let\'s schedule a quick bot walkthrough! Drop your email or needs: <a href="mailto:your-email@example.com?subject=Bot Demo Request" target="_blank">Email Me</a>. Pro tip: Mention "lead gen" for a custom sketch! 💬'
    elif intent == "info":
        ai_response = "<strong>All about my bots</strong>! Key perks: <em>Real-time sentiment analysis</em>, <strong>under 2s responses</strong>, seamless Vercel hosting. Ideal for client-facing apps. More deets? <a href='https://github.com/AquinasRousseau/sentiment-chatbot-api' target='_blank'>GitHub Repo</a>. What's your top feature ask?"
    elif intent == "support":
        ai_response = f"<em>Got your back</em>—sorry if you're <strong>{sentiment}</strong>! Bot glitch? Quick fixes: Refresh page or check console (F12). For custom help, hit me on Upwork. What's the snag? 🔧"
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
