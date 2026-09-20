import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"Key loaded: {'YES' if api_key else 'NO'}")
print("=" * 70)
print("AVAILABLE MODELS FOR YOUR KEY:")
print("=" * 70)

client = genai.Client(api_key=api_key)

try:
    for model in client.models.list():
        print(f"✅ {model.name}")
except Exception as e:
    print(f"❌ Error: {e}")