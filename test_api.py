# test_github.py
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load .env into os.environ
load_dotenv()

token = os.getenv("API_TOKEN")
if not token:
    raise ValueError("API_TOKEN is not set in .env")

model = os.getenv("API_MODEL", "deepseek/deepseek-r1:free")

client = OpenAI(
    base_url=os.environ.get("API_BASE_URL") or "https://openrouter.ai/api/v1"
    api_key=token
)

response = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "user", "content": "What is the book '1984' about in one paragraph?"}
    ],
    max_tokens=256
)

print(response.choices[0].message.content)
