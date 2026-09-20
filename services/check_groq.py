import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("=" * 70)
print("AVAILABLE GROQ MODELS:")
print("=" * 70)

try:
    for m in client.models.list().data:
        print(f"✅ {m.id}")
except Exception as e:
    print(f"❌ Error: {e}")