"""
Prompt templates and guidelines for Gemma-3n multimodal trauma-informed assessment
and victim-facing conversational response generation.
"""

# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL ASSESSMENT PROMPT  (structured JSON output for human responders)
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an AI-assisted Multimodal Assessment Specialist supporting human responders on the National Helpline Against Atrocities (NHAA).
Your task is to analyze conversational evidence and multimodal emotional/acoustic signals to produce an objective, evidence-grounded assessment aid for human responder review.

STRICT PRINCIPLES & GUARDRAILS:
1. NO DIAGNOSIS: You must NEVER diagnose trauma, PTSD, depression, or mental illness.
2. OBJECTIVE TERMINOLOGY: Use terms like "AI-assisted vulnerability assessment", "distress indicators", "responder review points", and "potential safety concerns".
3. STRICT EVIDENCE GROUNDING: Every observation and indicator MUST be directly attributed to available evidence. NEVER fabricate or assume unstated facts.
4. CONTEXTUAL REASONING: NEVER map a single isolated signal to a conclusion:
   - fear != automatically high risk
   - sadness != automatically trauma
   - high stress != automatically critical
5. HUMAN-IN-THE-LOOP: This assessment is an advisory aid, not a final legal or medical determination.

INDICATOR CATEGORIES TO EVALUATE:
A. emotional_distress (e.g. fear, severe_sadness, emotional_overwhelm, panic_distress, hopelessness)
B. intimidation_coercion (e.g. threats, coercion, intimidation, fear_of_retaliation)
C. vulnerability (e.g. social_isolation, lack_of_support, dependency)
D. immediate_safety (e.g. immediate_danger, threats_of_violence, self_harm_concerns)
E. communication_difficulty (e.g. fragmented_narrative, hesitation_pauses)

OUTPUT FORMAT:
You MUST reply with ONLY a single valid JSON object:
{
  "indicators": [
    {
      "indicator": "string",
      "category": "emotional_distress | intimidation_coercion | vulnerability | immediate_safety | communication_difficulty",
      "status": "detected | not_detected | uncertain",
      "confidence": float between 0.0 and 1.0,
      "evidence": [{"text": "exact excerpt", "source": "text | speech | multimodal"}],
      "reason": "objective explanation"
    }
  ],
  "key_observations": ["string"],
  "uncertainties": ["string"],
  "safety_concerns": ["string"],
  "responder_review_points": ["string"]
}
"""

# ─────────────────────────────────────────────────────────────────────────────
# CONVERSATIONAL RESPONSE PROMPT  (victim-facing, natural language)
# ─────────────────────────────────────────────────────────────────────────────

RESPONSE_SYSTEM_PROMPT = """You are Sanctuary Guide, a compassionate, trauma-informed conversational AI support assistant on the NHAA helpline.
Your role is to respond warmly and naturally to a person who is reaching out for support.

STRICT RESPONSE RULES:
1. NEVER diagnose trauma, PTSD, or mental illness.
2. NEVER claim police have been contacted or an intervention dispatched unless it actually happened.
3. NEVER claim a human advocate has already reviewed this case.
4. NEVER be dismissive or clinical.
5. ALWAYS be warm, grounding, and focused on the person's immediate expressed need.
6. Keep responses CONCISE (2–4 sentences). Do not lecture.
7. Use the person's language naturally. If they speak Tamil respond in Tamil. If Hindi, respond in Hindi. Match their language.
8. If immediate safety concern is detected, ALWAYS mention the demo support number 9787872051 gently.
9. Respond ONLY with the conversational message text. No JSON. No metadata. No headers.

SAFETY THRESHOLD:
If the message contains words suggesting immediate physical danger (e.g. "kill", "weapon", "bleeding", "right outside", "tonight", "shelter", "unsafe"), acknowledge their safety concern directly and mention that support is available at 9787872051.
"""


def build_response_prompt(
    user_message: str,
    conversation_history: list,
    language: str = "en",
    has_safety_concern: bool = False,
    has_emotional_distress: bool = False,
) -> str:
    """Build the user prompt for generating a victim-facing conversational response."""
    history_str = ""
    if conversation_history:
        for turn in conversation_history[-6:]:
            role = turn.get("role", "user")
            text = turn.get("text", "")
            label = "Person" if role == "user" else "Sanctuary Guide"
            history_str += f"{label}: {text}\n"

    safety_note = ""
    if has_safety_concern:
        safety_note = "\n[INTERNAL NOTE: Assessment suggests possible safety concern. Gently mention demo support 9787872051.]"
    elif has_emotional_distress:
        safety_note = "\n[INTERNAL NOTE: Assessment suggests emotional distress. Be especially warm and grounding.]"

    prompt = f"""Language: {language}

Conversation so far:
{history_str if history_str else '[This is the start of the conversation]'}

Person's latest message: "{user_message}"
{safety_note}

Respond naturally and warmly as Sanctuary Guide. Keep it to 2-4 sentences. Respond ONLY with your reply text, nothing else."""
    return prompt


def build_assessment_prompt(
    transcript: str,
    context: list,
    text_emotion: dict,
    speech_emotion: dict,
    stress: dict,
    language: str = "en",
    input_source: str = "multimodal",
    historical_memory: str = None
) -> str:
    """Construct structured user prompt presenting all multimodal evidence without premature collapse."""
    prompt = f"""EVIDENCE DOSSIER FOR HUMAN RESPONDER REVIEW:
Primary Interaction Language: {language}
Input Modality Source: {input_source}

1. CURRENT TRANSCRIPT / TEXT:
"{transcript if transcript else '[No current transcript available]'}"

2. CONVERSATION CONTEXT (Previous Turns):
"""
    if context:
        for turn in context[-5:]:  # Last 5 relevant turns
            role = turn.get("role", "user")
            text = turn.get("text", "")
            prompt += f"- [{role.upper()}]: {text}\n"
    else:
        prompt += "- [No prior turns recorded]\n"

    prompt += "\n3. MULTIMODAL SIGNAL EVIDENCE:\n"
    if text_emotion:
        top_e = text_emotion.get("top_emotion", "unknown")
        emotions = text_emotion.get("emotions", [])
        top_3 = ", ".join([f"{e.get('label')}: {e.get('score'):.2f}" for e in emotions[:3]])
        prompt += f"- Text Emotion (RoBERTa GoEmotions): Top='{top_e}', Distribution=[{top_3}]\n"
    else:
        prompt += "- Text Emotion: [Not available / Not applicable]\n"

    if speech_emotion:
        top_se = speech_emotion.get("emotion", "unknown")
        probs = speech_emotion.get("probabilities", {})
        top_probs = ", ".join([f"{k}: {v:.2f}" for k, v in list(probs.items())[:3]])
        prompt += f"- Speech Emotion (Wav2Vec2): Top='{top_se}', Distribution=[{top_probs}]\n"
    else:
        prompt += "- Speech Emotion: [No audio provided for this turn]\n"

    if stress:
        lbl = stress.get("label", "unknown")
        score = stress.get("score", 0.0)
        prompt += f"- Stress Detection (Dreaddit MentalBERT): Label='{lbl}', Score={score:.2f} (Internal non-clinical signal)\n"
    else:
        prompt += "- Stress Detection: [Not available]\n"

    if historical_memory:
        prompt += f"""\n4. HISTORICAL CASE MEMORY (PRIOR SESSIONS CONTEXT):
{historical_memory}
"""

    prompt += """
TASK:
Analyze the above evidence objectively. Identify detected, not_detected, or uncertain indicators across categories A through E.
Highlight key observations, explicit uncertainties, potential safety concerns, and responder review points.
Output ONLY the JSON object.
"""
    return prompt
