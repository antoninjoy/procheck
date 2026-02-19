import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load your API key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ Error: GOOGLE_API_KEY not found in .env")
else:
    genai.configure(api_key=api_key)
    print("🔍 Scanning for available embedding models...")
    try:
        # List all models that support embedding
        found = False
        for m in genai.list_models():
            if 'embedContent' in m.supported_generation_methods:
                print(f"✅ Available: {m.name}")
                found = True
        
        if not found:
            print("⚠️ No embedding models found. Check your API key permissions.")
    except Exception as e:
        print(f"❌ Error listing models: {e}")