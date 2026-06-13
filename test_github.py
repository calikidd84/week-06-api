# test_github.py
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load .env into os.environ
load_dotenv()

token = os.getenv("GITHUB_TOKEN")
if not token:
    raise ValueError("GITHUB_TOKEN is not set in .env")

model = os.getenv("GITHUB_MODEL", "openai/gpt-4.1")

client = OpenAI(
    base_url="https://models.github.ai/inference",
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
