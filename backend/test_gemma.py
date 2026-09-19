"""
Quick diagnostic script — tests Gemma HF inference directly.
Run from backend directory: python test_gemma.py
"""
import os
import sys

# Load env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
MODEL_ID = os.getenv("HF_CHAT_MODEL", "google/gemma-3-4b-it")

print(f"[DIAG] HF_TOKEN configured: {'YES (length=' + str(len(HF_TOKEN)) + ')' if HF_TOKEN else 'NO — MISSING'}")
print(f"[DIAG] Model: {MODEL_ID}")
print(f"[DIAG] Testing HuggingFace InferenceClient chat completion...")

try:
    from huggingface_hub import InferenceClient
    client = InferenceClient(token=HF_TOKEN)
    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Respond concisely."},
            {"role": "user", "content": "Respond with exactly: TrueVoice test successful."}
        ],
        max_tokens=50,
        temperature=0.1,
    )
    content = response.choices[0].message.content if response.choices else None
    if content:
        print(f"[DIAG] SUCCESS: GEMMA INFERENCE WORKED")
        print(f"[DIAG] Response: {content.strip()}")
    else:
        print("[DIAG] FAIL: GEMMA RETURNED EMPTY RESPONSE")
except Exception as e:
    print(f"[DIAG] FAIL: GEMMA INFERENCE FAILED")
    print(f"[DIAG] Error type: {type(e).__name__}")
    err = str(e)
    if "401" in err or "unauthorized" in err.lower():
        print("[DIAG] Category: 401 UNAUTHORIZED - HF token invalid or expired")
    elif "403" in err or "forbidden" in err.lower():
        print("[DIAG] Category: 403 FORBIDDEN - Model access denied")
    elif "404" in err or "not found" in err.lower():
        print("[DIAG] Category: 404 NOT FOUND - Model ID unavailable")
    elif "429" in err or "rate" in err.lower():
        print("[DIAG] Category: 429 RATE LIMITED")
    elif "timeout" in err.lower():
        print("[DIAG] Category: TIMEOUT")
    elif "connection" in err.lower() or "network" in err.lower():
        print("[DIAG] Category: NETWORK CONNECTION ERROR")
    elif "overloaded" in err.lower() or "busy" in err.lower():
        print("[DIAG] Category: MODEL OVERLOADED / BUSY")
    else:
        print(f"[DIAG] Category: UNKNOWN - {err[:300]}")

print("[DIAG] Done.")
