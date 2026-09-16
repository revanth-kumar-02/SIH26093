# SIH26093 — AI Disclosure & Model Card

## Non-Diagnostic Positioning Notice
The AI components in the SIH26093 platform function strictly as **decision-support and triage-prioritization aids** for trained helpline responders.
- The system **DOES NOT** provide clinical, medical, psychiatric, or psychological diagnoses.
- The system **DOES NOT** initiate autonomous police, medical, or legal emergency dispatch.
- Final authority and case actions remain exclusively in the hands of trained human responders.

## Component Disclosures

| Component | Model / Architecture | Deterministic? | Generative? | Human Review Required? | Primary Purpose |
|:---|:---|:---:|:---:|:---:|:---|
| **ASR** | `IndicConformer-600M` | Yes | No | Yes | Multilingual Indian speech-to-text |
| **SER** | `wav2vec2-emotion` | Yes | No | Yes | Speech prosody & acoustic emotion indicator |
| **TER** | `roberta-base-go_emotions` | Yes | No | Yes | 28-class text emotion detection |
| **Stress** | `mentalbert_dreaddit` | Yes | No | Yes | Textual stress prediction |
| **Assessment** | `gemma-3n-E2B-it` | No | Yes (Constrained) | Yes | Multimodal qualitative evidence synthesis |
| **SVI Engine** | Deterministic SVI v1.0 | Yes | No | Yes | Mathematical vulnerability scoring (0-100) |
