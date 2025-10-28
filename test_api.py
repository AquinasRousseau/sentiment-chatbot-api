import requests
import json

url = 'http://127.0.0.1:5000/analyze-chat'
headers = {'Content-Type': 'application/json', 'X-API-Key': 'devtestkey123'}

tests = [
    {'message': 'Love the new features!'},
    {'message': 'How do I reset password?'},
    {'message': 'App crashed again—frustrated!'}
]

for test in tests:
    response = requests.post(url, headers=headers, data=json.dumps(test))
    print(f"Input: {test['message']}\nOutput: {response.json()}\n---")
