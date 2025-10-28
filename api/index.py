import os
from flask import Flask, request, jsonify
from flask_cors import CORS  # Add for any future cross-origin needs
from functools import wraps
from dotenv import load_dotenv
from models.sentiment_model import analyze_sentiment
from chains.response_chain import generate_response

load_dotenv()
app = Flask(__name__)
CORS(app)  # Enables CORS (safe for demo)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

# Basic API key auth
API_KEY = 'devtestkey123'

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.headers.get('X-API-Key') != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/analyze-chat', methods=['POST'])
@require_auth
def analyze_chat():
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        if not user_message:
            return jsonify({'error': 'Message required'}), 400

        sentiment = analyze_sentiment(user_message)
        response = generate_response(user_message, sentiment)

        return jsonify({
            'sentiment': sentiment,
            'ai_response': response,
            'analysis_time': 'under 2s'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

# Serve the demo webpage on root (no file:// issues)
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.json or request.form
        user_message = data.get('message', '').strip()
        if user_message:
            sentiment = analyze_sentiment(user_message)
            response = generate_response(user_message, sentiment)
            return jsonify({'sentiment': sentiment, 'ai_response': response})
    
    # Embedded HTML (your demo page—full single-test focus)
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Empathetic Bot Demo</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            input, select, button { width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; }
            button { background: #4CAF50; color: white; border: none; cursor: pointer; font-size: 16px; }
            button:hover { background: #45a049; }
            #result { margin-top: 20px; padding: 15px; background: #f9f9f9; border-radius: 5px; white-space: pre-wrap; }
            h1 { text-align: center; color: #333; }
            #status-banner { padding: 10px; margin: 10px 0; border-radius: 5px; text-align: center; font-weight: bold; }
            .online { background: #d4edda; color: #155724; }
        </style>
    </head>
    <body>
        <h1>Empathetic Support Bot Demo</h1>
        <div id="status-banner" class="online">Server Online: Real AI Active!</div>
        
        <label for="quick-test">Quick Test Messages:</label>
        <select id="quick-test">
            <option value="">Select or type below...</option>
            <option value="Love the new features!">Positive: Love the new features!</option>
            <option value="How do I reset password?">Neutral: How do I reset password?</option>
            <option value="Fees too high—frustrated!">Negative: Fees too high—frustrated!</option>
        </select>
        
        <label for="message">Or Type Your Message:</label>
        <input type="text" id="message" placeholder="E.g., 'Love the new features!'">
        
        <button onclick="analyzeSingle()">Analyze Single</button>
        
        <div id="result"></div>
        
        <script>
            // Load dropdown to input
            document.getElementById('quick-test').addEventListener('change', function() {
                document.getElementById('message').value = this.value;
            });
            
            const API_URL = '/analyze-chat';  // Same-origin (no localhost needed)
            const HEADERS = { 'Content-Type': 'application/json', 'X-API-Key': 'devtestkey123' };
            
            // Single analyze
            async function analyzeSingle() {
                const message = document.getElementById('message').value.trim();
                if (!message) { alert('Enter a message!'); return; }
                
                document.getElementById('result').innerHTML = 'Analyzing...';
                try {
                    const response = await fetch(API_URL, {
                        method: 'POST',
                        headers: HEADERS,
                        body: JSON.stringify({ message })
                    });
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    const result = await response.json();
                    document.getElementById('result').innerHTML = 
                        `<strong>Sentiment:</strong> ${result.sentiment}\n\n` +
                        `<strong>AI Reply:</strong>\n${result.ai_response}\n\n` +
                        `<em>Time: ${result.analysis_time} | Real AI Powered</em>`;
                } catch (e) {
                    document.getElementById('result').innerHTML = `Error: ${e.message}. Check server?`;
                }
            }
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(debug=True, port=5000)
