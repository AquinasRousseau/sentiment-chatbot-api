 
import os
from flask import Flask, request, jsonify
from functools import wraps
from dotenv import load_dotenv
from models.sentiment_model import analyze_sentiment
from chains.response_chain import generate_response

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

# Basic API key auth (change for prod; simulates client security)
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

        # Step 1: Analyze sentiment
        sentiment = analyze_sentiment(user_message)

        # Step 2: Generate empathetic response
        response = generate_response(user_message, sentiment)

        return jsonify({
            'sentiment': sentiment,
            'ai_response': response,
            'analysis_time': 'under 2s'  # Placeholder
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
