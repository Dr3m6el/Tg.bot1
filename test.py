import requests
import os
from dotenv import load_dotenv

from main import OPENROUTER_API_KEY

load_dotenv()
key = os.getenv("OPENROUTER_API_KEY")

print(f"🔐 Using key: {key}")

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://yourdomain.com",   # ВАЖНО! Используй НЕ localhost, а реальный домен или пример
    "X-Title": "TelegramBot"
}

data = {
    "model": "qwen/qwen3-235b-a22b",
    "messages": [
        {"role": "user", "content": "Привет! Что такое искусственный интеллект?"}
    ]
}

response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

print(response.status_code)
print(response.text)
