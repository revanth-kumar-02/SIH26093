import json
import time
import re
import logging
from typing import Optional, Dict, Any, List
import httpx

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
    SUPPORT_PLAN_SYSTEM_PROMPT,
    build_assessment_prompt,
    build_response_prompt,
    build_support_plan_prompt,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class GemmaAdapter(BaseLLMAssessmentAdapter):
    """Production local LLM adapter for Gemma 3 12B IT conversational generation and assessment via Ollama / local runtime."""

    def __init__(
        self,
        model_id: Optional[str] = None,
        base_url: Optional[str] = None,
        runtime: Optional[str] = None,
        device: Optional[str] = None,
        timeout_seconds: Optional[float] = None
    ) -> None:
        self.model_id = model_id or settings.GEMMA_MODEL or settings.GEMMA_MODEL_ID
        self.base_url = (base_url or settings.GEMMA_BASE_URL).rstrip("/")
        self.runtime = runtime or settings.GEMMA_RUNTIME or "ollama"
        self.device = device or settings.GEMMA_DEVICE or "cpu"
        self.timeout_seconds = timeout_seconds or settings.GEMMA_TIMEOUT_SECONDS or 180.0
        self._is_loaded = False
        self._check_initial_reachability()

    def _check_initial_reachability(self) -> None:
        """Check if local inference runtime is reachable at startup."""
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    self._is_loaded = True
                    logger.info(
                        f"[GEMMA] Initialized LOCAL GemmaAdapter with model={self.model_id} "
                        f"on runtime={self.runtime} ({self.base_url})"
                    )
                    return
        except Exception as e:
            logger.warning(
                f"[GEMMA ERROR] Local runtime not reachable at {self.base_url} during init ({e}). "
                f"Ensure Ollama/llama.cpp is running locally."
            )
        self._is_loaded = False

    def is_loaded(self) -> bool:
        return self._is_loaded

    def warmup(self) -> None:
        """Verify local runtime connectivity and preload model."""
        self._check_initial_reachability()

    def unload(self) -> None:
        self._is_loaded = False

    def check_health(self) -> tuple[bool, Dict[str, Any]]:
        """Probe local runtime API to check readiness and available models."""
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    model_found = any(
                        self.model_id.lower() in m.lower() or m.lower().startswith("gemma")
                        for m in models
                    ) if models else True
                    self._is_loaded = True
                    return True, {"models": models, "target_model": self.model_id, "model_found": model_found}
        except Exception as e:
            self._is_loaded = False
            return False, {"error": str(e), "endpoint": self.base_url}
        return False, {"error": "Local runtime returned non-200", "endpoint": self.base_url}

    def _run_inference(
        self,
        system_prompt: str,
        user_prompt: str,
        max_new_tokens: int = 512,
        temperature: Optional[float] = None,
        messages: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Execute local chat completion against local inference runtime (Ollama HTTP API)."""
        logger.info("[GEMMA] provider = LOCAL")
        logger.info(f"[GEMMA] model = {self.model_id}")
        logger.info(f"[GEMMA] runtime = {self.runtime}")
        logger.info("[GEMMA] inference started")

        start_time = time.perf_counter()

        if messages is None:
            formatted_messages = []
            if system_prompt:
                formatted_messages.append({"role": "system", "content": system_prompt})
            if user_prompt:
                formatted_messages.append({"role": "user", "content": user_prompt})
        else:
            formatted_messages = messages

        eff_temperature = temperature if temperature is not None else settings.GEMMA_TEMPERATURE

        payload = {
            "model": self.model_id,
            "messages": formatted_messages,
            "stream": False,
            "options": {
                "temperature": eff_temperature,
                "num_predict": max_new_tokens,
                "num_ctx": settings.GEMMA_CONTEXT_LENGTH,
            }
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code != 200:
                    err_text = response.text[:200]
                    logger.error(
                        f"[GEMMA ERROR] Local runtime returned HTTP {response.status_code}: {err_text}"
                    )
                    raise RuntimeError(
                        f"Local Gemma runtime ({self.runtime}) returned HTTP {response.status_code}: {err_text}"
                    )

                data = response.json()
                msg = data.get("message", {})
                content = msg.get("content", "").strip()

                if not content:
                    logger.error("[GEMMA ERROR] Local Gemma returned empty content")
                    raise RuntimeError(f"Local Gemma model {self.model_id} produced empty response")

                duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
                eval_count = data.get("eval_count", 0)
                eval_duration_ns = data.get("eval_duration", 0)
                tok_per_sec = round(eval_count / (eval_duration_ns / 1e9), 2) if eval_duration_ns > 0 else 0.0

                logger.info("[GEMMA] inference completed")
                logger.info(
                    f"[GEMMA SUCCESS] model={self.model_id} duration={duration_ms}ms "
                    f"tokens={eval_count} speed={tok_per_sec}tok/s"
                )

                self._is_loaded = True
                return content

        except httpx.ConnectError as ce:
            self._is_loaded = False
            logger.error(f"[GEMMA ERROR] Local model unavailable at {self.base_url}: {ce}")
            raise RuntimeError(
                f"Local Gemma runtime unavailable at {self.base_url}. Please ensure {self.runtime} is running."
            ) from ce
        except httpx.TimeoutException as te:
            logger.error(f"[GEMMA ERROR] Local inference timed out after {self.timeout_seconds}s: {te}")
            raise RuntimeError(
                f"Local Gemma inference timed out after {self.timeout_seconds}s."
            ) from te
        except Exception as e:
            logger.error(f"[GEMMA ERROR] Inference failure: {e}")
            raise

    def assess(self, input_data: MultimodalAssessmentInput) -> TraumaAssessment:
        """Execute trauma-informed evidence assessment aid on multimodal signals."""
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

        logger.info(f"[GEMMA INVOCATION] session={input_data.session_id} — running local assessment inference")
        raw_output = self._run_inference(
            SYSTEM_PROMPT,
            user_prompt,
            max_new_tokens=settings.GEMMA_MAX_NEW_TOKENS,
            temperature=0.1
        )

        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        parsed_json = self._extract_json(raw_output)

        if not parsed_json:
            logger.warning("[GEMMA] Output did not contain valid JSON; constructing structured assessment from text")
            return self._build_error_fallback(input_data, raw_output, duration_ms)

        try:
            parsed_json["session_id"] = input_data.session_id
            parsed_json["model_version"] = self.model_id
            parsed_json["duration_ms"] = duration_ms
            parsed_json["device"] = self.device
            return TraumaAssessment.model_validate(parsed_json)
        except Exception as ve:
            logger.error(f"[GEMMA] Output schema validation error: {ve}")
            return self._build_error_fallback(input_data, raw_output, duration_ms)

    def analyze_completed_conversation(
        self,
        conversation_turns: List[dict],
        text_emotions: Optional[List[dict]] = None,
        stress_signals: Optional[List[dict]] = None,
        language: str = "en",
    ) -> dict:
        """Analyze full conversation context to extract grounded summary and indicators."""
        user_prompt = build_support_plan_prompt(
            conversation_turns=conversation_turns,
            text_emotions=text_emotions,
            stress_signals=stress_signals,
            language=language,
        )
        logger.info(f"[GEMMA INVOCATION] Running support plan full-conversation analysis (turns={len(conversation_turns)})")
        raw_output = self._run_inference(
            SUPPORT_PLAN_SYSTEM_PROMPT,
            user_prompt,
            max_new_tokens=450,
            temperature=0.3,
        )
        parsed = self._extract_json(raw_output)
        if parsed and isinstance(parsed, dict) and "what_we_heard" in parsed:
            logger.info("[GEMMA SUCCESS] Support plan analysis generated successfully via local Gemma")
            return parsed

        raise RuntimeError("Local Gemma failed to produce conformant support plan analysis JSON.")

    def generate_response(
        self,
        user_message: str,
        conversation_history: List[ConversationTurn],
        assessment: Optional[TraumaAssessment],
        language: str = "en",
        recent_assistant_openings: Optional[List[str]] = None,
        regeneration_directive: Optional[str] = None,
    ) -> str:
        """Generate a victim-facing empathetic conversational response using local Gemma 3 12B IT."""
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

        # Build full multi-turn messages array for chat endpoint
        messages = [{"role": "system", "content": RESPONSE_SYSTEM_PROMPT}]
        for turn in (conversation_history or []):
            role_str = "assistant" if turn.role in ("assistant", "ai", "system") else "user"
            messages.append({"role": role_str, "content": turn.text})

        # Append current user prompt containing context instructions
        messages.append({"role": "user", "content": user_prompt})

        logger.info(
            f"[GEMMA INVOCATION] language={language} turns={len(conversation_history or [])} "
            f"— running local conversational response inference"
        )

        raw_response = self._run_inference(
            system_prompt=RESPONSE_SYSTEM_PROMPT,
            user_prompt="",
            max_new_tokens=settings.GEMMA_MAX_NEW_TOKENS,
            temperature=settings.GEMMA_TEMPERATURE,
            messages=messages
        )

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

    def _build_error_fallback(
        self,
        input_data: MultimodalAssessmentInput,
        raw_text: str,
        duration_ms: float
    ) -> TraumaAssessment:
        return TraumaAssessment(
            session_id=input_data.session_id,
            indicators=[],
            key_observations=["Local model generation did not produce strictly conformant JSON."],
            uncertainties=["Local model JSON parse uncertainty; responder manual review recommended."],
            safety_concerns=["Review transcript manually."],
            responder_review_points=["Verify victim testimony directly with responder protocol."],
            model_version=self.model_id,
            duration_ms=duration_ms,
            device=self.device
        )
