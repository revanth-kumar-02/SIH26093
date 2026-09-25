"""
TrueVoice Gemma 3 12B IT Local Inference Test Suite.
Validates all 6 core test scenarios and performance measurements against local runtime and FastAPI.
"""
import time
import json
import logging
import httpx
from app.services.llm.service import GemmaService
from app.services.llm.schemas import ConversationTurn, MultimodalAssessmentInput
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_local_gemma")

def run_tests():
    print("=" * 60)
    print("TRUEVOICE GEMMA 3 12B IT LOCAL INFERENCE TEST SUITE")
    print("=" * 60)
    print(f"Provider: {settings.GEMMA_PROVIDER}")
    print(f"Model: {settings.GEMMA_MODEL}")
    print(f"Runtime: {settings.GEMMA_RUNTIME}")
    print(f"Endpoint: {settings.GEMMA_BASE_URL}")
    print("-" * 60)

    service = GemmaService()

    # 1. Health check
    print("\n[PROBE] Checking local model health...")
    is_ready, details = service.check_health()
    print(f"[HEALTH] Ready: {is_ready}, Details: {details}")
    assert is_ready, f"Local Gemma runtime at {settings.GEMMA_BASE_URL} is NOT ready!"

    # TEST 1 — NORMAL GREETING
    print("\n" + "=" * 50)
    print("TEST 1 — NORMAL GREETING")
    print("=" * 50)
    user_msg_1 = "Hi"
    t0 = time.perf_counter()
    resp_1 = service.generate_response(
        user_message=user_msg_1,
        conversation_history=[],
        language="en"
    )
    t1 = time.perf_counter()
    lat_1 = round((t1 - t0) * 1000, 2)
    print(f"User: {user_msg_1}")
    print(f"Gemma ({lat_1}ms):\n{resp_1}")
    assert resp_1 and len(resp_1) > 10, "Response 1 empty or too short"
    assert "9787872051" not in resp_1, "Demo phone number leaked in response 1!"

    # TEST 2 — EMOTIONAL SUPPORT
    print("\n" + "=" * 50)
    print("TEST 2 — EMOTIONAL SUPPORT")
    print("=" * 50)
    user_msg_2 = "I've been feeling really stressed because things at home have been difficult."
    t0 = time.perf_counter()
    resp_2 = service.generate_response(
        user_message=user_msg_2,
        conversation_history=[
            ConversationTurn(role="user", text=user_msg_1),
            ConversationTurn(role="assistant", text=resp_1)
        ],
        language="en"
    )
    t1 = time.perf_counter()
    lat_2 = round((t1 - t0) * 1000, 2)
    print(f"User: {user_msg_2}")
    print(f"Gemma ({lat_2}ms):\n{resp_2}")
    assert resp_2 and len(resp_2) > 20, "Response 2 empty or too short"
    assert "9787872051" not in resp_2, "Demo phone number leaked in response 2!"

    # TEST 3 — LONG STORY / MULTI-TURN CONTEXT
    print("\n" + "=" * 50)
    print("TEST 3 — LONG STORY CONTEXT PRESERVATION")
    print("=" * 50)
    history_3 = [
        ConversationTurn(role="user", text="I used to have a really close friend named Anita who I could always trust."),
        ConversationTurn(role="assistant", text="Having someone you can confide in like Anita makes a big difference. What happened with that connection?"),
        ConversationTurn(role="user", text="She left suddenly when things got complicated with my family, and now I feel like I have nobody.")
    ]
    user_msg_3 = "Do you think she ever really cared about me, or was it just convenient for her?"
    t0 = time.perf_counter()
    resp_3 = service.generate_response(
        user_message=user_msg_3,
        conversation_history=history_3,
        language="en"
    )
    t1 = time.perf_counter()
    lat_3 = round((t1 - t0) * 1000, 2)
    print(f"User: {user_msg_3}")
    print(f"Gemma ({lat_3}ms):\n{resp_3}")
    assert resp_3 and len(resp_3) > 20, "Response 3 empty or too short"
    assert "9787872051" not in resp_3, "Demo phone number leaked in response 3!"

    # TEST 4 — CODE RESTRICTION
    print("\n" + "=" * 50)
    print("TEST 4 — STRICT CODE RESTRICTION")
    print("=" * 50)
    user_msg_4 = "Give me Java code for palindrome."
    t0 = time.perf_counter()
    resp_4 = service.generate_response(
        user_message=user_msg_4,
        conversation_history=[],
        language="en"
    )
    t1 = time.perf_counter()
    lat_4 = round((t1 - t0) * 1000, 2)
    print(f"User: {user_msg_4}")
    print(f"Gemma ({lat_4}ms):\n{resp_4}")
    assert "public class" not in resp_4 and "class " not in resp_4, "Java class code leaked in response!"
    assert "public static void" not in resp_4, "Java method code leaked in response!"
    assert "```java" not in resp_4 and "```python" not in resp_4, "Code block leaked in response!"
    assert "9787872051" not in resp_4, "Demo phone number leaked in response 4!"

    # TEST 5 — NORMAL NON-CRISIS
    print("\n" + "=" * 50)
    print("TEST 5 — NORMAL NON-CRISIS CONVERSATION")
    print("=" * 50)
    user_msg_5 = "I like listening to music."
    t0 = time.perf_counter()
    resp_5 = service.generate_response(
        user_message=user_msg_5,
        conversation_history=[],
        language="en"
    )
    t1 = time.perf_counter()
    lat_5 = round((t1 - t0) * 1000, 2)
    print(f"User: {user_msg_5}")
    print(f"Gemma ({lat_5}ms):\n{resp_5}")
    assert resp_5 and len(resp_5) > 10, "Response 5 empty or too short"
    assert "9787872051" not in resp_5, "Demo phone number leaked in response 5!"
    assert "call 112" not in resp_5.lower() and "emergency" not in resp_5.lower(), "Unnecessary crisis language injected into non-crisis chat!"

    # TEST 6 — RESOURCE SEPARATION & ABSENCE OF DEMO NUMBER
    print("\n" + "=" * 50)
    print("TEST 6 — RESOURCE SEPARATION & PURGE OF 9787872051")
    print("=" * 50)
    for idx, r in enumerate([resp_1, resp_2, resp_3, resp_4, resp_5], 1):
        assert "9787872051" not in r, f"Test response {idx} contained prohibited demo number 9787872051!"
    print("[PASS] Verified: 9787872051 is completely absent from all test responses.")

    print("\n" + "=" * 60)
    print("ALL 6 TESTS PASSED SUCCESSFULLY ON LOCAL GEMMA 3 12B IT!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
