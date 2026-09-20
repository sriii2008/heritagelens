import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("=" * 70)
print("AVAILABLE MODELS FOR YOUR API KEY:")
print("=" * 70)

try:
    for m in genai.list_models():
        print(f"✅ {m.name}")
        print(f"   Methods: {m.supported_generation_methods}")
        print()
except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("Possible causes:")
    print("1. API key is wrong in .env file")
    print("2. API key is not activated yet (wait a few minutes)")
    print("3. Internet connection issue")