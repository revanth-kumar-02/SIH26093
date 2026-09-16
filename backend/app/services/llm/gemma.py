import json
import time
import re
import logging
from typing import Optional, Dict, Any, List
from app.services.llm.base import BaseLLMAssessmentAdapter
from app.services.llm.schemas import (
    MultimodalAssessmentInput,
    TraumaAssessment,
    AssessmentIndicator,
    EvidenceItem
)
from app.services.llm.prompts import SYSTEM_PROMPT, build_assessment_prompt
from app.core.config import settings
from app.core.telemetry import resolve_device, get_system_resources

logger = logging.getLogger(__name__)

class GemmaAdapter(BaseLLMAssessmentAdapter):
    """Production LLM adapter for Gemma-3n-E2B-it multimodal assessment."""

    def __init__(self, model_id: Optional[str] = None, device: Optional[str] = None) -> None:
        self.model_id = model_id or settings.GEMMA_MODEL_ID
        self.device = resolve_device(device or settings.GEMMA_DEVICE)
        self._tokenizer = None
        self._model = None
        self._is_loaded = False
        logger.info(f"Initialized GemmaAdapter with model_id={self.model_id} on {self.device}")

    def is_loaded(self) -> bool:
        return self._is_loaded

    def warmup(self) -> None:
        self._load()

    def unload(self) -> None:
        self._tokenizer = None
        self._model = None
        self._is_loaded = False
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    def _load(self) -> None:
        if not self._is_loaded:
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM
            start_t = time.perf_counter()
            logger.info(f"Loading Gemma model: {self.model_id} on {self.device}...")
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_id,
                token=settings.HF_TOKEN
            )
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                token=settings.HF_TOKEN,
                torch_dtype=torch.bfloat16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None
            )
            if self.device != "cuda":
                self._model.to(self.device)
            self._model.eval()
            self._is_loaded = True
            load_ms = round((time.perf_counter() - start_t) * 1000.0, 2)
            res = get_system_resources()
            logger.info(f"Gemma model loaded in {load_ms}ms. RAM RSS: {res.get('ram_rss_mb')} MB")

    def assess(self, input_data: MultimodalAssessmentInput) -> TraumaAssessment:
        self._load()
        import torch

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

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        if hasattr(self._tokenizer, "apply_chat_template"):
            full_prompt = self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
        else:
            full_prompt = f"{SYSTEM_PROMPT}\n\nUser:\n{user_prompt}\n\nAssistant:"

        inputs = self._tokenizer(full_prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            output_tokens = self._model.generate(
                **inputs,
                max_new_tokens=settings.GEMMA_MAX_NEW_TOKENS,
                temperature=settings.GEMMA_TEMPERATURE,
                do_sample=settings.GEMMA_TEMPERATURE > 0.0,
                pad_token_id=self._tokenizer.eos_token_id
            )

        new_tokens = output_tokens[0][inputs["input_ids"].shape[-1]:]
        raw_output = self._tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        # Parse JSON
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
        # Guardrail: Communication difficulty is NOT treated as proof of trauma!
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
