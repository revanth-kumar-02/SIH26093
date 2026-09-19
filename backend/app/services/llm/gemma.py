import json
import time
import re
import logging
from typing import Optional, Dict, Any, List
from huggingface_hub import InferenceClient
from app.services.llm.base import BaseLLMAssessmentAdapter
from app.services.llm.schemas import (
    MultimodalAssessmentInput,
    TraumaAssessment,
    AssessmentIndicator,
    EvidenceItem,
    ConversationTurn,
)
from app.services.llm.prompts import (
    SYSTEM_PROMPT,
    RESPONSE_SYSTEM_PROMPT,
    build_assessment_prompt,
    build_response_prompt,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class GemmaAdapter(BaseLLMAssessmentAdapter):
    """Production remote LLM adapter for Gemma conversational generation and assessment via Hugging Face InferenceClient."""

    def __init__(
        self,
        model_id: Optional[str] = None,
        token: Optional[str] = None,
        device: Optional[str] = None
    ) -> None:
        self.model_id = model_id or settings.HF_CHAT_MODEL or settings.GEMMA_MODEL_ID
        # Map legacy unsupported model ID if specified
        if self.model_id == "google/gemma-3n-E2B-it":
            self.model_id = "google/gemma-3-4b-it"
        self.device = device or settings.GEMMA_DEVICE
        self._token = token or settings.HF_TOKEN
        self._client: Optional[InferenceClient] = None
        self._is_loaded = False
        self._init_client()

    def _init_client(self) -> None:
        if self._token:
            self._client = InferenceClient(token=self._token)
            self._is_loaded = True
            logger.info(f"Initialized remote GemmaAdapter with model_id={self.model_id} via Hugging Face InferenceClient")
        else:
            logger.warning("GemmaAdapter initialized without HF_TOKEN; remote inference will be unauthenticated")
            self._client = InferenceClient()
            self._is_loaded = False

    def is_loaded(self) -> bool:
        return self._is_loaded

    def warmup(self) -> None:
        """Verify remote inference connection with a lightweight probe."""
        if not self._client:
            self._init_client()

    def unload(self) -> None:
        self._client = None
        self._is_loaded = False

    def _run_inference(
        self,
        system_prompt: str,
        user_prompt: str,
        max_new_tokens: int = 512,
        temperature: Optional[float] = None
    ) -> Optional[str]:
        """Remote chat completion via Hugging Face InferenceClient with retry backoff."""
        if not self._client:
            self._init_client()

        logger.info("[AI] Gemma request started")
        logger.info(f"[AI] Model: {self.model_id}")
        logger.info("[AI] Provider: Hugging Face")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        candidate_models = []
        # Prioritize free serverless Gemma models to prevent 402 Payment Required errors
        pref = self.model_id if self.model_id and self.model_id not in ("google/gemma-3-12b-it", "google/gemma-3-27b-it") else "google/gemma-3-4b-it"
        candidate_models.append(pref)
        for alt in ["google/gemma-3-4b-it", "google/gemma-3-1b-it"]:
            if alt not in candidate_models:
                candidate_models.append(alt)

        eff_temperature = temperature if temperature is not None else settings.GEMMA_TEMPERATURE
        last_err = None
        for current_model in candidate_models:
            max_retries = 2
            backoff_seconds = 1.0

            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"[AI] Attempting Gemma inference with model={current_model} (attempt {attempt})")
                    response = self._client.chat.completions.create(
                        model=current_model,
                        messages=messages,
                        max_tokens=max_new_tokens,
                        temperature=eff_temperature
                    )
                    if response and response.choices and len(response.choices) > 0:
                        content = response.choices[0].message.content
                        if content:
                            logger.info(f"[AI] Inference succeeded with {current_model}")
                            logger.info(
                                f"[REAL GEMMA INFERENCE] model={current_model} "
                                f"[AI RESPONSE] provider=huggingface model={current_model} source=real_inference"
                            )
                            return content.strip()
                    raise ValueError(f"Empty choices in response from {current_model}")

                except Exception as e:
                    last_err = e
                    err_msg = str(e)
                    if "402" in err_msg or "payment" in err_msg.lower() or "credits" in err_msg.lower():
                        logger.warning(f"[REAL GEMMA INFERENCE] Model {current_model} requires credits (402), switching to next model...")
                        break

                    is_transient = "429" in err_msg or "overloaded" in err_msg.lower() or "busy" in err_msg.lower() or "timeout" in err_msg.lower()
                    if is_transient:
                        logger.warning(
                            f"[REAL GEMMA INFERENCE RETRY] model={current_model} attempt={attempt}/{max_retries} "
                            f"transient_error={err_msg[:120]}, switching or retrying in {backoff_seconds}s..."
                        )
                        time.sleep(backoff_seconds)
                        backoff_seconds *= 2
                        if attempt == max_retries:
                            break
                        continue

                    # Non-transient error on this model, try next candidate
                    logger.warning(f"[REAL GEMMA INFERENCE] Model {current_model} failed with non-transient error: {err_msg[:120]}")
                    break

        logger.error("[AI] Inference FAILED on all candidate Gemma models")
        logger.error(f"[AI] Error type: {type(last_err).__name__}")
        logger.error(
            f"[REAL GEMMA INFERENCE FAILED] models={candidate_models} "
            f"error_type={type(last_err).__name__} error={str(last_err)[:200]}"
        )
        if last_err:
            raise last_err
        raise RuntimeError("Gemma inference failed on all candidate models")


    def assess(self, input_data: MultimodalAssessmentInput) -> TraumaAssessment:
        start_time = time.perf_counter()

        user_prompt = build_assessment_prompt(
            transcript=input_data.transcript or "",
            context=[turn.model_dump() for turn in input_data.conversation_context],
            text_emotion=input_data.text_emotion.model_dump() if input_data.text_emotion else {},
            speech_emotion=input_data.speech_emotion.model_dump() if input_data.speech_emotion else {},
            stress=input_data.stress.model_dump() if input_data.stress else {},
            language=input_data.language or "en",
            input_source=input_data.input_source or "multimodal",
            historical_memory=input_data.historical_memory
        )

        logger.info(f"[GEMMA INVOCATION] session={input_data.session_id} — running assessment inference")
        raw_output = None
        try:
            raw_output = self._run_inference(SYSTEM_PROMPT, user_prompt, max_new_tokens=settings.GEMMA_MAX_NEW_TOKENS)
        except Exception as e:
            raise RuntimeError(f"Gemma remote assessment failed: {e}") from e

        if not raw_output:
            raise RuntimeError("Gemma remote assessment returned empty output.")

        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        logger.info(f"[GEMMA SUCCESS] assessment inference done in {duration_ms}ms, raw_len={len(raw_output)}")

        parsed_json = self._extract_json(raw_output)
        if not parsed_json:
            logger.warning("Gemma did not return valid JSON; using structured fallback schema")
            return self._build_error_fallback(input_data, raw_output, duration_ms)

        try:
            parsed_json["session_id"] = input_data.session_id
            parsed_json["model_version"] = self.model_id
            parsed_json["duration_ms"] = duration_ms
            parsed_json["device"] = self.device
            return TraumaAssessment.model_validate(parsed_json)
        except Exception as ve:
            logger.error(f"Gemma output validation error: {ve}")
            return self._build_error_fallback(input_data, raw_output, duration_ms)

    def generate_response(
        self,
        user_message: str,
        conversation_history: List[ConversationTurn],
        assessment: Optional[TraumaAssessment],
        language: str = "en",
        recent_assistant_openings: Optional[List[str]] = None,
        regeneration_directive: Optional[str] = None,
    ) -> str:
        """Generate a victim-facing empathetic conversational response using Gemma via remote HF inference."""
        start_time = time.perf_counter()

        has_safety_concern = False
        has_emotional_distress = False
        if assessment:
            has_safety_concern = bool(assessment.safety_concerns)
            has_emotional_distress = any(
                ind.status == "detected" and ind.category == "emotional_distress"
                for ind in assessment.indicators
            )

        history_dicts = [{"role": t.role, "text": t.text} for t in (conversation_history or [])]
        user_prompt = build_response_prompt(
            user_message=user_message,
            conversation_history=history_dicts,
            language=language,
            has_safety_concern=has_safety_concern,
            has_emotional_distress=has_emotional_distress,
            recent_assistant_openings=recent_assistant_openings,
            regeneration_directive=regeneration_directive,
        )

        logger.info(f"[GEMMA INVOCATION] language={language} — running conversational response inference")
        raw_response = None
        try:
            # Temperature 0.65 provides natural human emotional diversity while remaining grounded
            raw_response = self._run_inference(
                RESPONSE_SYSTEM_PROMPT,
                user_prompt,
                max_new_tokens=300,
                temperature=0.65
            )
        except Exception as e:
            raise RuntimeError(f"Gemma conversational inference failed: {e}") from e

        if not raw_response:
            raise RuntimeError("Gemma conversational inference returned empty response.")

        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        response_text = raw_response.strip()
        logger.info(
            f"[GEMMA SUCCESS] response inference done in {duration_ms}ms, "
            f"response_len={len(response_text)}"
        )

        return response_text


    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        candidate = match.group(1) if match else text
        try:
            return json.loads(candidate.strip())
        except Exception:
            s = text.find("{")
            e = text.rfind("}")
            if s != -1 and e != -1 and e > s:
                try:
                    return json.loads(text[s:e+1])
                except Exception:
                    pass
        return None

    def _build_error_fallback(self, input_data: MultimodalAssessmentInput, raw_text: str, duration_ms: float) -> TraumaAssessment:
        return TraumaAssessment(
            session_id=input_data.session_id,
            indicators=[],
            key_observations=["Raw model generation did not produce strictly conformant JSON."],
            uncertainties=["Model generation parse failure; manual responder inspection required."],
            safety_concerns=["Review raw transcript manually."],
            responder_review_points=["Verify victim testimony directly with responder protocol."],
            model_version=self.model_id,
            duration_ms=duration_ms,
            device=self.device
        )


class MockGemmaAdapter(BaseLLMAssessmentAdapter):
    """Deterministic, rule-based trauma-informed multimodal reasoning adapter for offline testing.

    Guarantees strict schema adherence, zero hallucinations, and faithful evidence grounding.
    """

    def __init__(self, device: str = "cpu") -> None:
        self.device = device
        self._is_loaded = True
        self.model_id = "mock-gemma-3n-E2B-it"

    def is_loaded(self) -> bool:
        return True

    def warmup(self) -> None:
        pass

    def unload(self) -> None:
        pass

    def assess(self, input_data: MultimodalAssessmentInput) -> TraumaAssessment:
        start_t = time.perf_counter()

        text_content = (input_data.transcript or "").lower()
        context_text = " ".join([t.text.lower() for t in input_data.conversation_context])
        full_text = f"{text_content} {context_text}"

        indicators: List[AssessmentIndicator] = []
        observations: List[str] = []
        uncertainties: List[str] = []
        safety_concerns: List[str] = []
        review_points: List[str] = []

        # ----------------------------------------------------
        # Category A: Emotional Distress
        # ----------------------------------------------------
        distress_evidence: List[EvidenceItem] = []
        has_distress_kw = any(k in full_text for k in ["terrified", "fear", "scared", "shaking", "panic", "crying", "anxious", "anxiety", "hurt"])
        has_sadness_kw = any(k in full_text for k in ["hopeless", "sad", "depressed", "worthless", "broken"])

        if input_data.transcript and has_distress_kw:
            distress_evidence.append(EvidenceItem(text=input_data.transcript[:100], source="text"))

        if input_data.speech_emotion and input_data.speech_emotion.emotion in ["fearful", "sad", "angry"]:
            distress_evidence.append(EvidenceItem(
                text=f"Acoustic classification indicates elevated {input_data.speech_emotion.emotion} speech signal",
                source="speech"
            ))

        if input_data.stress and input_data.stress.label == "stressed":
            distress_evidence.append(EvidenceItem(
                text=f"Dreaddit stress marker detected (confidence {input_data.stress.score:.2f})",
                source="multimodal"
            ))

        if distress_evidence:
            indicators.append(AssessmentIndicator(
                indicator="acute_emotional_distress",
                category="emotional_distress",
                status="detected",
                confidence=0.88 if len(distress_evidence) >= 2 else 0.72,
                evidence=distress_evidence,
                reason="Verbal expressions of fear or anxiety corroborated by acoustic or text-stress evidence."
            ))
            observations.append("Elevated emotional distress signals observed across available modalities.")
        elif has_sadness_kw:
            indicators.append(AssessmentIndicator(
                indicator="prolonged_sadness",
                category="emotional_distress",
                status="detected",
                confidence=0.68,
                evidence=[EvidenceItem(text=input_data.transcript[:100] if input_data.transcript else "Reported feelings of hopelessness", source="text")],
                reason="Self-reported expressions of hopelessness without immediate panic markers."
            ))
        else:
            indicators.append(AssessmentIndicator(
                indicator="acute_emotional_distress",
                category="emotional_distress",
                status="not_detected",
                confidence=0.80,
                evidence=[],
                reason="No overt verbal or acoustic markers of acute emotional overwhelm detected in current exchange."
            ))

        # ----------------------------------------------------
        # Category B: Intimidation & Coercion
        # ----------------------------------------------------
        coercion_evidence: List[EvidenceItem] = []
        intimidation_keywords = ["threat", "kill", "harm", "stalk", "retaliat", "blackmail", "track", "harass", "monitor", "listen to my calls"]
        matching_coercion = [w for w in intimidation_keywords if w in full_text]

        if matching_coercion and input_data.transcript:
            coercion_evidence.append(EvidenceItem(text=input_data.transcript, source="text"))
            indicators.append(AssessmentIndicator(
                indicator="intimidation_and_threats",
                category="intimidation_coercion",
                status="detected",
                confidence=0.91,
                evidence=coercion_evidence,
                reason=f"Explicit verbal reports of coercive tactics or threats ({', '.join(matching_coercion)})."
            ))
            observations.append("Complainant reports direct threats and surveillance intimidation.")
            safety_concerns.append("Reported intimidation and threats of retaliation against complainant.")
        else:
            indicators.append(AssessmentIndicator(
                indicator="intimidation_and_threats",
                category="intimidation_coercion",
                status="not_detected",
                confidence=0.75,
                evidence=[],
                reason="No explicit mentions of threats, stalking, or coercion in provided narrative."
            ))

        # ----------------------------------------------------
        # Category C: Vulnerability & Isolation
        # ----------------------------------------------------
        vulnerability_evidence: List[EvidenceItem] = []
        if any(k in full_text for k in ["nowhere to go", "no family", "alone", "isolated", "no money", "depend", "shelter"]):
            vulnerability_evidence.append(EvidenceItem(text=input_data.transcript or "Expressed lack of secure shelter", source="text"))
            indicators.append(AssessmentIndicator(
                indicator="social_and_material_vulnerability",
                category="vulnerability",
                status="detected",
                confidence=0.82,
                evidence=vulnerability_evidence,
                reason="Complainant explicitly references absence of safe shelter or personal support network."
            ))
            observations.append("Identified vulnerability regarding safe shelter options and support network.")
            review_points.append("Verify availability of verified emergency shelter resources with human responder.")
        else:
            indicators.append(AssessmentIndicator(
                indicator="social_and_material_vulnerability",
                category="vulnerability",
                status="not_detected",
                confidence=0.70,
                evidence=[],
                reason="No current indicators of acute isolation or shelter deprivation documented."
            ))

        # ----------------------------------------------------
        # Category D: Immediate Safety Concerns
        # ----------------------------------------------------
        imminent_danger_kw = ["kill me", "right outside", "at the door", "weapon", "knife", "gun", "bleeding", "tonight", "emergency"]
        has_imminent = any(k in full_text for k in imminent_danger_kw)

        if has_imminent and input_data.transcript:
            indicators.append(AssessmentIndicator(
                indicator="imminent_physical_danger",
                category="immediate_safety",
                status="detected",
                confidence=0.94,
                evidence=[EvidenceItem(text=input_data.transcript, source="text")],
                reason="Narrative contains statements indicating immediate, active threat to physical safety."
            ))
            safety_concerns.append("Immediate physical proximity or lethal threats flagged for urgent human responder review.")
            review_points.append("Prioritize live responder triage; confirm physical safety without automating police dispatch.")
        else:
            indicators.append(AssessmentIndicator(
                indicator="imminent_physical_danger",
                category="immediate_safety",
                status="not_detected",
                confidence=0.85,
                evidence=[],
                reason="No indication of active in-progress physical attack in current input."
            ))

        # ----------------------------------------------------
        # Category E: Communication Difficulty
        # ----------------------------------------------------
        if len(text_content.strip()) < 15 or "..." in text_content or any(p in text_content for p in ["i don't know", "can't speak", "hard to explain"]):
            indicators.append(AssessmentIndicator(
                indicator="fragmented_or_hesitant_communication",
                category="communication_difficulty",
                status="detected",
                confidence=0.75,
                evidence=[EvidenceItem(text=input_data.transcript or "Brief hesitant utterance", source="text")],
                reason="Utterance contains brief or hesitant phrasing. Note: This is an acoustic/text observation and does not prove trauma."
            ))
            observations.append("Communication hesitation or brevity observed; gentle open-ended pacing recommended.")
        else:
            indicators.append(AssessmentIndicator(
                indicator="fragmented_or_hesitant_communication",
                category="communication_difficulty",
                status="not_detected",
                confidence=0.80,
                evidence=[],
                reason="Narrative flow is coherent and articulate."
            ))

        # ----------------------------------------------------
        # Uncertainties & Modality Cross-Checks
        # ----------------------------------------------------
        if input_data.speech_emotion is None:
            uncertainties.append("Speech emotion signal unavailable (text-only input). Acoustic veracity and vocal prosody cannot be corroborated.")
        if input_data.text_emotion is None:
            uncertainties.append("Text emotion distribution unavailable.")
        if input_data.stress is None:
            uncertainties.append("Dreaddit stress marker unavailable.")

        if not review_points:
            review_points.append("Human responder review recommended to confirm situational context before initiating referral pathways.")

        duration_ms = round((time.perf_counter() - start_t) * 1000.0, 2)

        return TraumaAssessment(
            session_id=input_data.session_id,
            indicators=indicators,
            key_observations=observations,
            uncertainties=uncertainties,
            safety_concerns=safety_concerns,
            responder_review_points=review_points,
            model_version=self.model_id,
            duration_ms=duration_ms,
            device=self.device
        )

    def generate_response(
        self,
        user_message: str,
        conversation_history: List[ConversationTurn],
        assessment: Optional[TraumaAssessment],
        language: str = "en",
        recent_assistant_openings: Optional[List[str]] = None,
        regeneration_directive: Optional[str] = None,
    ) -> str:
        """Generate a context-aware victim-facing response based on message content and assessment."""
        start_t = time.perf_counter()
        lang = language.strip().lower()
        lower = user_message.lower()

        # Determine if there is a safety concern from assessment
        has_safety_concern = False
        if assessment and assessment.safety_concerns:
            has_safety_concern = True

        # Build conversation awareness — does the history contain prior context?
        history_len = len(conversation_history) if conversation_history else 0

        # Detect key themes in current message
        is_privacy = any(k in lower for k in ["anonymous", "privacy", "secret", "private", "confidential", "encrypted", "trace"])
        is_greeting = any(k in lower for k in ["hi", "hello", "hey", "my name", "i'm ", "i am "]) and len(lower) < 60
        has_friend_support = any(k in lower for k in ["friend", "stay with", "can stay", "staying with"])
        needs_shelter = any(k in lower for k in ["shelter", "safe place", "nowhere to go", "home tonight", "stay tonight", "place tonight"])
        has_threat = any(k in lower for k in ["threat", "kill", "harm", "weapon", "stalk", "danger", "attack", "hurt me"])
        has_fear = any(k in lower for k in ["scared", "fear", "terrified", "afraid", "panic", "anxious", "anxiety"])
        needs_legal = any(k in lower for k in ["legal", "police", "fir", "court", "rights", "lawyer", "law"])
        wants_to_talk = any(k in lower for k in ["talk", "speak", "someone to talk", "listen", "hear me"])
        expresses_distress = any(k in lower for k in ["don't know", "lost", "hopeless", "can't", "exhausted", "tired", "anymore"])
        is_unclear_or_gibberish = (len(lower.split()) == 1 and len(lower) > 4 and not any(v in lower for v in ["help", "stop", "safe", "scared", "hello", "threat", "shelter"])) or bool(re.search(r"[bcdfghjklmnpqrstvwxyz]{5,}", lower))

        duration_ms = round((time.perf_counter() - start_t) * 1000.0, 2)

        # Generate contextually appropriate response
        def respond(en: str, ta: str = "", hi: str = "", te: str = "") -> str:
            if lang.startswith("ta") and ta:
                return ta
            if lang.startswith("hi") and hi:
                return hi
            if lang.startswith("te") and te:
                return te
            return en

        # 1. Unclear / hesitant / gibberish input
        if is_unclear_or_gibberish:
            return respond(
                en=(
                    "I didn't quite catch that, but I'm right here with you. "
                    "Please take all the time you need—you can type or speak whenever you feel ready, and share only what feels safe."
                ),
                ta=(
                    "நீங்கள் கூறியது சரியாக புரியவில்லை, ஆனால் நான் உங்களுடன் இருக்கிறேன். "
                    "அவசரமில்லை—உங்களுக்கு வசதியான நேரத்தில் நீங்கள் பேசலாம்."
                ),
                hi=(
                    "मैं आपकी बात पूरी तरह समझ नहीं पाया, लेकिन मैं आपके साथ हूँ। "
                    "आराम से समय लें—जब भी सहज महसूस करें, आप अपनी बात साझा कर सकते हैं।"
                ),
            )

        # 2. Privacy / Confidentiality inquiry
        if is_privacy:
            return respond(
                en=(
                    "Yes, this conversation is completely confidential and protected with end-to-end trauma-informed privacy protocols. "
                    "You are in full control of what you share and when. No identifying information is shared without your explicit consent."
                ),
                ta=(
                    "ஆம், இந்த உரையாடல் முற்றிலும் ரகசியமானது மற்றும் பாதுகாப்பானது. "
                    "நீங்கள் பகிர்வதை மட்டுமே நாங்கள் சேமிக்கிறோம். உங்கள் வெளிப்படையான ஒப்புதல் இல்லாமல் எந்த தகவலும் பகிரப்படாது."
                ),
                hi=(
                    "हाँ, यह बातचीत पूरी तरह से गोपनीय और सुरक्षित है। "
                    "आप जो भी साझा करते हैं वह सुरक्षित रहता है। आपकी सहमति के बिना कोई भी जानकारी साझा नहीं की जाएगी।"
                ),
            )

        # 3. Greetings and self-introductions
        if is_greeting and history_len <= 1:
            name_part = ""
            for phrase in ["i'm ", "i am ", "my name is ", "im "]:
                if phrase in lower:
                    rest = lower.split(phrase)[-1].strip().split()[0].rstrip(".,!")
                    if rest and len(rest) > 1 and rest.lower() not in ["here", "scared", "tired", "fine", "feeling"]:
                        name_part = f", {rest.capitalize()}"
                        break
            return respond(
                en=(
                    f"Hello{name_part}. You've reached a safe, confidential space. "
                    "You can share as much or as little as you'd like, whenever you're ready. "
                    "How can we support you today?"
                ),
                ta=(
                    f"வணக்கம்{name_part}. நீங்கள் ஒரு பாதுகாப்பான, நம்பகமான இடத்தை அடைந்திருக்கிறீர்கள். "
                    "உங்களுக்கு வசதியான நேரத்தில் பேசலாம். இன்று நாங்கள் உங்களுக்கு எவ்வாறு உதவலாம்?"
                ),
                hi=(
                    f"नमस्ते{name_part}। आप एक सुरक्षित और विश्वसनीय स्थान पर हैं। "
                    "जितना आप सहज महसूस करें, उतना साझा करें। आज हम आपकी क्या सहायता कर सकते हैं?"
                ),
            )

        # 4. Friend / Informal Support System (e.g. "My friend said I can stay with her")
        if has_friend_support:
            return respond(
                en=(
                    "Having a supportive friend and a safe place to go is an important step. "
                    "You are in complete control of your next steps. Would you like to explore additional safety planning or confidential resources while you're there?"
                ),
                ta=(
                    "உங்களுக்கு ஆதரவான ஒரு நண்பர் மற்றும் தங்குவதற்கு பாதுகாப்பான இடம் இருப்பது ஒரு முக்கியமான படி. "
                    "அங்கு இருக்கும்போது உங்களுக்கு கூடுதல் பாதுகாப்பு திட்டம் அல்லது வழிகாட்டுதல் தேவையா?"
                ),
                hi=(
                    "एक मददगार दोस्त और ठहरने के लिए सुरक्षित जगह होना एक बहुत महत्वपूर्ण कदम है। "
                    "क्या आप वहाँ रहते हुए आगे की सुरक्षा योजना या सहायता संसाधनों के बारे में जानना चाहेंगे?"
                ),
            )

        # 5. Emergency threats and shelter needs (e.g. "I'm scared to go home tonight")
        if has_threat or needs_shelter or (has_safety_concern and any(k in lower for k in ["unsafe", "danger", "help", "home tonight"])):
            return respond(
                en=(
                    "We hear you, and your safety matters deeply to us right now. "
                    "You've taken a brave step by reaching out. "
                    "If you're in immediate need of safe shelter or emergency assistance tonight, please reach out to local emergency services or a trusted support line — "
                    "trained advocates and support services are available to assist you."
                ),
                ta=(
                    "நாங்கள் உங்கள் பாதுகாப்பை மிகவும் முக்கியமாக கருதுகிறோம். "
                    "நீங்கள் துணிச்சலாக உதவி கோரியிருக்கிறீர்கள். "
                    "உடனடி பாதுகாப்பான தங்குமிடம் அல்லது அவசர உதவி தேவைப்பட்டால், அவசர உதவி சேவைகளை தொடர்பு கொள்ளுங்கள்."
                ),
                hi=(
                    "हम आपकी बात सुन रहे हैं और आपकी सुरक्षा हमारी सर्वोच्च प्राथमिकता है। "
                    "यदि आपको तत्काल सुरक्षित आश्रय या सहायता की आवश्यकता है, तो कृपया आपातकालीन सहायता सेवाओं से संपर्क करें।"
                ),
            )

        # 6. Legal / Rights inquiry
        if needs_legal:
            return respond(
                en=(
                    "I hear you. Navigating legal processes or police reporting can feel overwhelming, and you have every right to understand your protections. "
                    "Under the National Helpline Against Atrocities (NHAA) framework, we can connect you with confidential pro-bono legal support whenever you're ready."
                ),
                ta=(
                    "சட்டப் பிரச்சினைகள் மற்றும் உரிமைகள் பற்றிய உங்கள் கேள்விகளை நாங்கள் புரிந்துகொள்கிறோம். "
                    "தேசிய வன்கொடுமை தடுப்பு உதவி மையம் (NHAA) மூலமாக உங்களுக்கு இலவச சட்ட ஆலோசனை வழங்க முடியும்."
                ),
                hi=(
                    "कानूनी प्रक्रियाएं समझना कठिन हो सकता है। "
                    "राष्ट्रीय अत्याचार निवारण हेल्पलाइन (NHAA) के तहत हम आपको निःशुल्क एवं गोपनीय कानूनी सलाह से जोड़ सकते हैं।"
                ),
            )

        # 7. Fear and emotional distress (e.g. "I'm feeling scared")
        if has_fear:
            return respond(
                en=(
                    "It sounds like you're going through something really frightening right now, and I want you to know you don't have to face this alone. "
                    "Can you tell me a little more about what's been happening, whenever you feel ready?"
                ),
                ta=(
                    "இப்போது நீங்கள் மிகவும் பயமாக உணர்கிறீர்கள் என்று புரிகிறது. நீங்கள் தனியாக இல்லை. "
                    "உங்களுக்கு வசதியாக இருக்கும்போது, என்ன நடந்தது என்று கொஞ்சம் சொல்லுங்கள்."
                ),
                hi=(
                    "ऐसा लगता है आप अभी बहुत डरे हुए हैं — आप अकेले नहीं हैं। "
                    "जब तैयार हों, तो मुझे बताएं क्या हो रहा है।"
                ),
            )

        if wants_to_talk:
            return respond(
                en=(
                    "I'm glad you reached out. This is a safe space, and I'm here to listen without judgment. "
                    "Take your time — you can start wherever feels right."
                ),
                ta=(
                    "நீங்கள் தொடர்பு கொண்டதில் மகிழ்ச்சி. நான் உங்கள் பேச்சை கேட்கிறேன், எந்த தீர்ப்பும் இல்லாமல். "
                    "உங்கள் வேகத்தில் தொடங்குங்கள்."
                ),
                hi=(
                    "मुझे खुशी है कि आपने संपर्क किया। यह एक सुरक्षित जगह है, बिना किसी निर्णय के। "
                    "जब चाहें शुरू करें।"
                ),
            )

        if expresses_distress:
            return respond(
                en=(
                    "What you're feeling right now makes complete sense given what you're going through. "
                    "You reached out, and that took courage. "
                    "I'm here — can you tell me more about what's been happening?"
                ),
                ta=(
                    "நீங்கள் இப்போது உணர்வது முற்றிலும் இயற்கையானது. நீங்கள் உதவி கோரியது தைரியமான செயல். "
                    "என்ன நடந்தது என்று என்னிடம் சொல்லுங்கள்."
                ),
                hi=(
                    "आप जो महसूस कर रहे हैं वह बिल्कुल स्वाभाविक है। आपने यहाँ आना हिम्मत का काम किया। "
                    "मुझे बताएं क्या हो रहा है।"
                ),
            )

        # Default: warm, open, context-sensitive
        if history_len > 2:
            return respond(
                en=(
                    "Thank you for continuing to share with me. "
                    "I'm listening carefully, and everything you say helps us better understand how to support you. "
                    "Please go on whenever you're ready."
                ),
                ta=(
                    "தொடர்ந்து பகிர்ந்துகொண்டிருப்பதற்கு நன்றி. நான் கவனமாக கேட்கிறேன். "
                    "உங்கள் வேகத்தில் தொடரலாம்."
                ),
                hi=(
                    "साझा करते रहने के लिए धन्यवाद। मैं ध्यान से सुन रहा हूँ। "
                    "जब भी तैयार हों, आगे बताएं।"
                ),
            )

        return respond(
            en=(
                "Thank you for trusting us and sharing your experience. We are listening closely, and you can share as much or as little as feels comfortable. "
                "Take all the time you need — we are here to support you."
            ),
            ta=(
                "எங்களை நம்பி உங்கள் அனுபவத்தை பகிர்ந்ததற்கு நன்றி. உங்கள் சொந்த வேகத்தில் பேசலாம். நாங்கள் எப்போதும் உங்களுடன் இருக்கிறோம்."
            ),
            hi=(
                "अपनी बात साझा करने के लिए धन्यवाद। हम ध्यान से सुन रहे हैं। आराम से समय लें, हम आपके साथ हैं।"
            ),
        )

