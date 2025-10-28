# Empathetic Support Bot API

Flask API: Analyzes sentiment (TensorFlow/RoBERTa) and generates tailored responses (LangChain/OpenAI).

## Setup
1. `pip install -r requirements.txt`
2. Set `.env` with OPENAI_API_KEY.
3. `python app.py` → Test at http://127.0.0.1:5000.

## Usage
POST /analyze-chat: `{"message": "..."}` + X-API-Key: devtestkey123
Example: curl -X POST ... -d '{"message": "Fees too high!"}'

## Tech
- Sentiment: Transformers + TF 2.20
- Responses: LangChain + GPT-4o-mini

Built by [Your Name]—AI integration specialist.
