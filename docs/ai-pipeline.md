# SIH26093 — AI Pipeline Architecture

The AI pipeline is 100% locked and strictly layered:

## Layer 1: Speech-to-Text (ASR)
- **Model:** `ai4bharat/indic-conformer-600m-multilingual`
- **Architecture:** Hybrid CTC + RNNT multilingual conformer.
- **Languages:** 22 scheduled Indian languages (Hindi, Tamil, Telugu, Kannada, Bengali, Marathi, etc.) + English.
- **Input:** 16 kHz single-channel mono PCM audio.

## Layer 2: Signal Extraction (Emotion & Stress)
- **Speech Emotion Recognition (SER):** `Dpngtm/wav2vec2-emotion-recognition` (7 classes: anger, disgust, fear, happiness, neutral, sadness, surprise).
- **Text Emotion Recognition (TER):** `SamLowe/roberta-base-go_emotions` (28 fine-grained emotion classes).
- **Stress Detection:** `jtvallente/mentalbert_dreaddit_best` (Dreaddit-trained MentalBERT binary stress classifier with probability calibration).

## Layer 3: Multimodal Synthesis & Evidence Grounding
- **Model:** `google/gemma-3n-E2B-it`
- **Role:** Synthesizes multimodal acoustic signals, textual transcripts, and conversation history into typed qualitative evidence indicators.
- **Strict Boundary:** Gemma is **NOT** allowed to compute risk scores or trigger external dispatch.

## Layer 4: Deterministic SVI Engine v1.0
- Computes mathematical Stress Vulnerability Index (0.0 - 100.0) based on weighted evidence categories:
  - Immediate Physical Safety (Weight: 35.0)
  - Intimidation & Coercion (Weight: 25.0)
  - Emotional Distress & Despair (Weight: 20.0)
  - Systemic / Social Vulnerability (Weight: 20.0)
- **Anti-Inflation Rule:** Duplicate indicators from the same modality are capped.
- **Independence:** Immediate safety flags operate independently of the numerical SVI score.
