import os
import requests

api_key = os.environ.get("TOGETHER_API_KEY")

url = "https://api.together.xyz/v1/chat/completions"  # chat endpoint

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    # Pick a serverless model:
    # "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
    # "meta-llama/Meta-Llama-3-8B-Instruct"
    # "mistralai/Mixtral-8x7B-Instruct-v0.1"
    "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is 2 + 2? Answer with just the number."}
    ],
    "max_tokens": 20,
    "temperature": 0
}

resp = requests.post(url, headers=headers, json=data)
print("Status:", resp.status_code)
try:
    print("Response:", resp.json())
except Exception as e:
    print("Raw text:", resp.text)
