import requests
import json
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def create_session(lang="en"):
    res = requests.post(f"{BASE_URL}/api/v1/sessions", json={"language": lang}, timeout=10)
    res.raise_for_status()
    return res.json()["session_id"]

def send_message(session_id, message, input_source="TEXT"):
    res = requests.post(
        f"{BASE_URL}/api/v1/sessions/{session_id}/messages",
        json={"message": message, "input_source": input_source},
        timeout=75
    )
    res.raise_for_status()
    return res.json()["response"]

def run_tests():
    print("==================================================")
    print("TRUEVOICE REAL GEMMA CONVERSATION QUALITY SUITE")
    print("==================================================\n")

    # TEST A: Simple Stress
    print("--- RUNNING TEST A: SIMPLE STRESS ---")
    sess_a = create_session()
    msg_a = "Today I feel very stressed."
    print(f"User: {msg_a}")
    t0 = time.time()
    resp_a = send_message(sess_a, msg_a)
    print(f"TrueVoice Guide ({round(time.time() - t0, 1)}s):\n{resp_a}\n")
    time.sleep(3)

    # TEST B: Long Personal Story (with follow up to test multi-turn story continuity)
    print("--- RUNNING TEST B: LONG PERSONAL STORY ---")
    sess_b = create_session()
    msg_b1 = "I had many friends like Swetha, Alima and Joswin, but Anita was different. With her I felt safe and comfortable. At the end of the day she left me behind and now I keep thinking about what happened."
    print(f"User Turn 1: {msg_b1}")
    t0 = time.time()
    resp_b1 = send_message(sess_b, msg_b1)
    print(f"TrueVoice Guide Turn 1 ({round(time.time() - t0, 1)}s):\n{resp_b1}\n")
    time.sleep(3)

    # Turn 2 follow up checking continuity ("she" refers to Anita)
    msg_b2 = "Why do you think she did that after making me feel so safe?"
    print(f"User Turn 2: {msg_b2}")
    t0 = time.time()
    resp_b2 = send_message(sess_b, msg_b2)
    print(f"TrueVoice Guide Turn 2 ({round(time.time() - t0, 1)}s):\n{resp_b2}\n")
    time.sleep(3)

    # TEST C: Abuse / Coercion
    print("--- RUNNING TEST C: ABUSE / COERCION ---")
    sess_c = create_session()
    msg_c = "I want to live with my family but my relatives are forcing me to stay with them and they eventually abuse me."
    print(f"User: {msg_c}")
    t0 = time.time()
    resp_c = send_message(sess_c, msg_c)
    print(f"TrueVoice Guide ({round(time.time() - t0, 1)}s):\n{resp_c}\n")
    time.sleep(3)

    # TEST D: Normal Topic
    print("--- RUNNING TEST D: NORMAL TOPIC ---")
    sess_d = create_session()
    msg_d = "I like listening to music when I'm alone."
    print(f"User: {msg_d}")
    t0 = time.time()
    resp_d = send_message(sess_d, msg_d)
    print(f"TrueVoice Guide ({round(time.time() - t0, 1)}s):\n{resp_d}\n")
    time.sleep(3)

    # TEST E: Coding Redirection
    print("--- RUNNING TEST E: CODING REDIRECTION ---")
    sess_e = create_session()
    msg_e = "Give me Java code for palindrome."
    print(f"User: {msg_e}")
    t0 = time.time()
    resp_e = send_message(sess_e, msg_e)
    print(f"TrueVoice Guide ({round(time.time() - t0, 1)}s):\n{resp_e}\n")

    print("==================================================")
    print("ALL SCENARIOS EXECUTED")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
