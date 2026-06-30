import sys
import os

# Add the groq_app directory to Python path so it can find 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from dotenv import load_dotenv

load_dotenv()

from app.core.llm import generate_json

async def test_groq():
    token = os.environ.get('GROQ_API_KEY')
    print(f"GROQ_API_KEY length: {len(token) if token else 0}")
    if not token or token == "your_groq_api_key_here":
        print("Please provide a real GROQ_API_KEY in the .env file first!")
        return

    prompt = "Generate a JSON object with a single key 'message' and the value 'Hello from Groq!'"
    print("Testing Groq LLM connection...")
    try:
        result = await generate_json(prompt)
        print("Success! Received:")
        print(result)
    except Exception as e:
        print("Failed!")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_groq())
