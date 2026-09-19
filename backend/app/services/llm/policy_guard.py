"""
TrueVoice Policy Guard: Request Classification, Output Sanitization, and Code Restrictions.
Enforces strict boundaries so that the real Gemma model never generates code, diagnoses,
or unsolicited emergency phone numbers.
"""

import re
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Predefined safe policy redirection responses
CODE_REDIRECTION_MESSAGES = {
    "en": "I can help with support and conversation, but I can't provide programming or coding assistance here. If you'd like, tell me what's been going on and we can focus on that.",
    "hi": "मैं यहाँ आपको भावनात्मक सहयोग और मार्गदर्शन प्रदान करने के लिए हूँ, लेकिन मैं प्रोग्रामिंग या कोडिंग सहायता प्रदान नहीं कर सकता। यदि आप चाहें, तो मुझे बता सकते हैं कि आप क्या महसूस कर रहे हैं और हम उस पर बात कर सकते हैं।",
    "ta": "நான் உங்களுக்கு ஆதரவும் உரையாடலும் வழங்க இங்கே இருக்கிறேன், ஆனால் நிரலாக்க (coding) உதவிகளை என்னால் வழங்க முடியாது. நீங்கள் விரும்பினால், உங்கள் மனநிலையைப் பற்றி என்னிடம் பகிர்ந்து கொள்ளலாம்.",
    "te": "నేను మీకు మద్దతు మరియు సంభాషణతో సహాయపడగలను, కానీ నేను ఇక్కడ ప్రోగ్రామింగ్ లేదా కోడింగ్ సహాయాన్ని అందించలేను. మీకు కావాలంటే, ఏమి జరుగుతుందో నాకు చెప్పండి మరియు మనం దానిపై దృష్టి పెట్టవచ్చు.",
    "kn": "ನಾನು ನಿಮಗೆ ಬೆಂಬಲ ಮತ್ತು ಸಂಭಾಷಣೆಯೊಂದಿಗೆ ಸಹಾಯ ಮಾಡಬಲ್ಲೆ, ಆದರೆ ನಾನು ಇಲ್ಲಿ ಪ್ರೋಗ್ರಾಮಿಂಗ್ ಅಥವಾ ಕೋಡಿಂಗ್ ಸಹಾಯವನ್ನು ನೀಡಲು ಸಾಧ್ಯವಿಲ್ಲ. ನೀವು ಬಯಸಿದರೆ, ಏನು ನಡೆಯುತ್ತಿದೆ ಎಂದು ನನಗೆ ತಿಳಿಸಿ ಮತ್ತು ನಾವು ಅದರ ಮೇಲೆ ಗಮನ ಹರಿಸಬಹುದು.",
    "ml": "എനിക്ക് പിന്തുണയും സംഭാഷണവും നൽകാൻ കഴിയും, എന്നാൽ ഇവിടെ പ്രോഗ്രാമിംഗ് അല്ലെങ്കിൽ കോഡിംഗ് സഹായം നൽകാൻ കഴിയില്ല. എന്താണ് സംഭവിക്കുന്നതെന്ന് പങ്കുവെക്കാമെങ്കിൽ നമുക്ക് അതിൽ ശ്രദ്ധ കേന്ദ്രീകരിക്കാം.",
}

# Regex patterns matching programming and coding requests
CODE_REQUEST_PATTERNS = [
    # Explicit language + code/program/script/query
    r"\b(?:write|give|show|create|generate|provide|send|need|want)\s+(?:me\s+)?(?:a\s+)?(?:code|program|script|query|algorithm|solution|function|class)\b",
    r"\b(?:code|program|script|query|function|algorithm|implementation)\s+(?:in|for|using|with)\s+(?:java|python|c\+\+|cpp|c\b|c#|javascript|typescript|js|ts|dart|flutter|sql|html|css|php|rust|golang|go|ruby|bash|shell|powershell)",
    r"\b(?:java|python|c\+\+|cpp|c#|javascript|typescript|js|ts|dart|flutter|sql|html|css|php|rust|golang|ruby|bash|shell|powershell)\s+(?:code|program|script|query|function|class|algorithm|developer|implementation)",
    # Palindrome & algorithm specifics
    r"\b(?:code\s+for\s+palindrome|palindrome\s+(?:code|program|in\s+java|in\s+python|in\s+c))\b",
    r"\b(?:palindrome|palindromes)\b",
    r"\b(?:reverse\s+a\s+string\s+in|fibonacci\s+(?:in|series\s+in)|binary\s+search\s+in|linked\s+list\s+in)\b",
    # Debugging / technical queries
    r"\b(?:debug|fix|compile|run|refactor)\s+(?:my\s+)?(?:code|script|program|query|flutter|dart|python|java|c\+\+)\b",
    r"\b(?:how\s+(?:to|do\s+i)\s+(?:code|program|implement|write)\s+(?:a\s+)?(?:function|class|api|script|sql|query|algorithm))\b",
    r"\b(?:sql\s+query|select\s+\*\s+from|insert\s+into|update\s+set|delete\s+from|drop\s+table)\b",
    r"\b(?:give\s+me\s+in\s+one\s+language|in\s+one\s+language)\b",
]

# Patterns for conversational context follow-ups that imply code continuation
CONTEXT_CODE_TRIGGERS = [
    r"\b(?:just\s+(?:in\s+)?(?:python|java|c|c\+\+|javascript|dart))\b",
    r"\b(?:in\s+(?:python|java|c|c\+\+|javascript|dart)\s+only)\b",
    r"\b(?:or\s+give\s+me\s+in\s+one\s+language)\b",
    r"\b(?:give\s+me\s+in\s+(?:python|java|c|c\+\+|javascript|dart))\b",
    r"\b(?:show\s+me\s+the\s+code)\b",
]

# Compiled regex for fast matching
COMPILED_CODE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in CODE_REQUEST_PATTERNS]
COMPILED_CONTEXT_TRIGGERS = [re.compile(p, re.IGNORECASE) for p in CONTEXT_CODE_TRIGGERS]

# Output code detection patterns
OUTPUT_CODE_PATTERNS = [
    re.compile(r"```[a-zA-Z0-9_-]*\s*[\s\S]*?```"),  # Markdown code blocks
    re.compile(r"\bpublic\s+static\s+void\s+main\b"),
    re.compile(r"\bpublic\s+class\s+[A-Za-z0-9_]+"),
    re.compile(r"\bSystem\.out\.print(?:ln)?\s*\("),
    re.compile(r"#include\s*<[a-zA-Z0-9_.]+>"),
    re.compile(r"\bdef\s+[a-zA-Z0-9_]+\s*\([^)]*\)\s*:"),
    re.compile(r"\bconsole\.log\s*\("),
    re.compile(r"\bSELECT\s+[\s\S]+?\s+FROM\s+[a-zA-Z0-9_]+", re.IGNORECASE),
    re.compile(r"\bimport\s+java\.[a-zA-Z0-9_.]+;"),
    re.compile(r"\bfrom\s+[a-zA-Z0-9_]+\s+import\s+[a-zA-Z0-9_*]+"),
    re.compile(r"\bint\s+main\s*\([^)]*\)\s*\{"),
]

# Clinical diagnosis statements to sanitize
CLINICAL_DIAGNOSIS_PATTERNS = [
    (re.compile(r"\byou\s+have\s+(?:depression|ptsd|clinical\s+depression|trauma|anxiety\s+disorder|a\s+mental\s+illness)\b", re.IGNORECASE),
     "it sounds like you are experiencing significant emotional distress"),
    (re.compile(r"\byou\s+are\s+(?:clinically\s+depressed|traumatized|suffering\s+from\s+ptsd)\b", re.IGNORECASE),
     "you are carrying a lot of heavy feelings right now"),
]

# Hardcoded demo phone number to scrub from normal conversational output
DEMO_PHONE_NUMBER = "9787872051"
PHONE_REGEX = re.compile(r"(?:support\s+is\s+available\s+(?:right\s+now\s+)?(?:at\s+)?|call\s+(?:us\s+at\s+)?|contact\s+(?:us\s+at\s+)?|helpline\s+(?:at\s+)?)?9787872051[—\s-]*", re.IGNORECASE)


def is_programming_request(text: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> bool:
    """Classify whether the user message is asking for code, programming, or technical implementation."""
    if not text:
        return False

    clean_text = text.strip()

    # Direct match on current message
    for pattern in COMPILED_CODE_PATTERNS:
        if pattern.search(clean_text):
            return True

    # Check context-dependent follow-up triggers if conversation history contains code requests
    for pattern in COMPILED_CONTEXT_TRIGGERS:
        if pattern.search(clean_text):
            return True

    # Check if recent history had a code query and current message is short follow-up
    if conversation_history:
        recent_turns = conversation_history[-3:]
        recent_code_activity = False
        for turn in recent_turns:
            turn_text = turn.get("text", "") or turn.get("content", "")
            if any(p.search(turn_text) for p in COMPILED_CODE_PATTERNS):
                recent_code_activity = True
                break

        if recent_code_activity:
            lowered = clean_text.lower()
            if any(k in lowered for k in ["python", "java", "c++", "c language", "one language", "show me", "write it", "give code"]):
                return True

    return False


def get_code_redirection_response(language: str = "en") -> str:
    """Return the predefined safe supportive redirection response in the requested language."""
    lang_key = (language or "en").lower()[:2]
    return CODE_REDIRECTION_MESSAGES.get(lang_key, CODE_REDIRECTION_MESSAGES["en"])


def is_code_in_output(text: str) -> bool:
    """Check if the generated LLM text contains executable code, code blocks, or technical syntax."""
    if not text:
        return False

    for pattern in OUTPUT_CODE_PATTERNS:
        if pattern.search(text):
            return True

    return False


def sanitize_response_output(
    text: str,
    language: str = "en",
    allow_emergency_contacts: bool = False
) -> str:
    """Sanitize and guard Gemma's response before returning it to the user.
    
    1. Replaces unexpected code generation with the safe redirection message.
    2. Strips hardcoded/unsolicited phone numbers (like 9787872051).
    3. Rewords clinical diagnostic claims into trauma-informed observational support.
    4. Strips false professional identity claims.
    """
    if not text:
        return ""

    # Output Guard: Detect code blocks or code patterns
    if is_code_in_output(text):
        logger.warning("[AI] Output guard: CODE_DETECTED — replacing with safe redirection")
        return get_code_redirection_response(language)

    sanitized = text

    # Remove hardcoded 9787872051 if not explicitly authorized by verified emergency layer
    if not allow_emergency_contacts and DEMO_PHONE_NUMBER in sanitized:
        logger.info(f"[AI] Sanitizing unsolicited phone number from response")
        sanitized = PHONE_REGEX.sub("", sanitized)
        # Clean up any trailing broken phrases like "Please know that ." or "available at ."
        sanitized = re.sub(r"\b(?:available\s+at|reach\s+out\s+at|contact\s+at|support\s+at)\s*\.?", "", sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r"\s*\.\s*\.", ".", sanitized)
        sanitized = re.sub(r"\s+([.,!?;])", r"\1", sanitized)
        sanitized = re.sub(r"\s{2,}", " ", sanitized).strip()
        # Ensure proper punctuation at the end
        if sanitized and not sanitized.endswith((".", "!", "?")):
            sanitized += "."

    # Sanitize clinical diagnosis claims
    for diag_pattern, replacement in CLINICAL_DIAGNOSIS_PATTERNS:
        if diag_pattern.search(sanitized):
            logger.info("[AI] Sanitizing clinical diagnostic statement into observational support")
            sanitized = diag_pattern.sub(replacement, sanitized)

    # Sanitize false professional claims
    sanitized = re.sub(
        r"\b(?:I\s+am|I'm)\s+(?:a\s+doctor|your\s+doctor|a\s+therapist|your\s+therapist|a\s+psychologist|a\s+police\s+officer|a\s+lawyer)\b",
        "I am TrueVoice Guide, an AI-assisted support guide",
        sanitized,
        flags=re.IGNORECASE
    )

    return sanitized.strip()


# ─────────────────────────────────────────────────────────────────────────────
# LIGHTWEIGHT QUALITY CHECK & ANTI-REPETITION EVALUATOR
# ─────────────────────────────────────────────────────────────────────────────

GENERIC_CLICHES = [
    (re.compile(r"\bthat sounds (?:like an? )?(?:incredibly|deeply|so|very)?\s*(?:painful|difficult|hurtful|tough|heavy|overwhelming|challenging)\b", re.IGNORECASE),
     "generic empathy opening ('That sounds incredibly...')"),
    (re.compile(r"\bit takes (?:a lot of |so much )?(?:courage|strength) to share\b", re.IGNORECASE),
     "generic validation cliché ('It takes courage/strength to share')"),
    (re.compile(r"\byou don't have to (?:carry|face) this (?:burden |alone)?(?:alone)?\b", re.IGNORECASE),
     "formulaic phrase ('You don't have to carry this alone')"),
    (re.compile(r"\b(?:would you like to|do you want to)\s+(?:talk|tell me)\s+(?:more\b|about\s+how\s+you(?:'re|\s+are)\s+feeling)\b", re.IGNORECASE),
     "generic closing question ('Would you like to talk/tell me more')"),
    (re.compile(r"\bthank you for (?:sharing|opening up|reaching out)\b", re.IGNORECASE),
     "polite conversational filler ('Thank you for sharing')"),
    (re.compile(r"\bi'm so sorry (?:that )?you(?:'re|\s+are) going through this\b", re.IGNORECASE),
     "formulaic apology ('I'm so sorry you're going through this')"),
]


class QualityCheckResult:
    """Result of lightweight response quality evaluation."""
    def __init__(self, is_acceptable: bool, issues: List[str], directive: str = ""):
        self.is_acceptable = is_acceptable
        self.issues = issues
        self.directive = directive

    def __repr__(self) -> str:
        return f"<QualityCheckResult acceptable={self.is_acceptable} issues={self.issues}>"


def evaluate_response_quality(
    response: str,
    user_message: str,
    recent_assistant_openings: Optional[List[str]] = None
) -> QualityCheckResult:
    """Evaluates response for repetitive generic clichés and lack of narrative grounding.
    
    Returns QualityCheckResult. If not acceptable, includes an actionable directive
    for a single targeted regeneration by Real Gemma.
    """
    if not response or not response.strip():
        return QualityCheckResult(
            is_acceptable=False,
            issues=["empty_response"],
            directive="Provide a warm, attentive response (2-4 sentences) acknowledging the user's situation."
        )

    clean_resp = response.strip()
    issues = []

    # Check for generic clichés
    detected_cliches = []
    for pattern, description in GENERIC_CLICHES:
        if pattern.search(clean_resp):
            detected_cliches.append(description)

    # Check if opening sentence relies immediately on a generic template
    first_sentence = clean_resp.split(".")[0].strip() if "." in clean_resp else clean_resp
    first_pattern = GENERIC_CLICHES[0][0]
    starts_with_generic = bool(first_pattern.search(first_sentence))

    if starts_with_generic:
        issues.append("starts_with_generic_cliche")

    # If 2 or more cliches are detected, flag as overly formulaic
    if len(detected_cliches) >= 2:
        issues.append(f"multiple_cliches_detected: {', '.join(detected_cliches)}")

    # Check for repeated openings from recent assistant turns
    if recent_assistant_openings:
        resp_words = clean_resp.lower().split()[:5]
        resp_prefix = " ".join(resp_words)
        for prev_opening in recent_assistant_openings:
            prev_words = prev_opening.lower().split()[:5]
            prev_prefix = " ".join(prev_words)
            if resp_prefix and prev_prefix and resp_prefix == prev_prefix:
                issues.append(f"repeated_recent_opening: '{resp_prefix}'")
                break

    if not issues:
        return QualityCheckResult(is_acceptable=True, issues=[])

    # Build targeted directive for regeneration
    critique_items = []
    if starts_with_generic:
        critique_items.append("Do NOT start with 'That sounds incredibly...' or any formulaic empathy opener.")
    if detected_cliches:
        critique_items.append(f"Avoid formulaic phrases like: {', '.join(detected_cliches)}.")
    critique_items.append(
        "Speak directly and specifically about the actual people, events, or situation mentioned in: "
        f"'{user_message[:100]}...'. Respond with authentic, grounded human reflection."
    )

    directive = " ".join(critique_items)
    return QualityCheckResult(is_acceptable=False, issues=issues, directive=directive)

