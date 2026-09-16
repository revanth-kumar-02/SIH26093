# SIH26093 — Presentation & Demonstration Guide

## Demonstration Manifest (Synthetic Scenarios)
All scenarios use synthetic, non-sensitive fictional data. Notice: **DEMO / SYNTHETIC DATA**.

- **Case A (Low Vulnerability):** `NHAA-2026-SYN-0825` — General procedural compensation inquiry. SVI: 18.0 (LOW). Routine brochure recommendation.
- **Case B (Moderate Vulnerability):** `NHAA-2026-SYN-0820` — Neighborhood friction and isolation in Hindi. SVI: 45.0 (MODERATE). Community counseling callback.
- **Case C (High Vulnerability):** `NHAA-2026-SYN-0815` — Workplace retaliatory intimidation and economic coercion. SVI: 72.0 (HIGH). Legal aid (DLSA) referral.
- **Case D (Urgent Safety Review):** `NHAA-2026-SYN-0812` — Active intruder / domestic threat at residence. SVI: 88.5 (CRITICAL). Immediate safety flags triggered. Emergency human desk escalation.
- **Case E (Multiple Recommendations):** `NHAA-2026-SYN-0830` — In-law harassment and threatened eviction with minors in Tamil. SVI: 71.0 (HIGH). 3 pathways: Psychological First Aid, Legal Aid, Shelter Coordination.

## Live SIH Demo Script (16 Steps)
1. **App Launch:** Open Flutter client (Android / Web).
2. **Language Selection:** Choose preferred language (English, Hindi, Tamil).
3. **Consent & Privacy:** Display clear informed consent emphasizing AI assistance and non-replacement of human responders.
4. **Start Intake:** Open conversational sanctuary chat.
5. **Voice Input:** Record voice narrative or speak live.
6. **ASR Display:** Show IndicConformer real-time transcription.
7. **Signal Generation:** Show backend extraction of SER, TER, and Dreaddit stress.
8. **Gemma Assessment:** Display structured evidence indicators with attributed sources.
9. **SVI Calculation:** Demonstrate deterministic score generation and factor breakdown.
10. **Risk Triage:** Show assigned risk category (LOW, MODERATE, HIGH, CRITICAL).
11. **Recommendations:** Review generated advisory pathways.
12. **Responder Login:** Switch to Responder Console; log in with ADMIN credentials (`admin_user`). (PEOPLE credentials `people_user` are denied admin portal with HTTP 403).
13. **Queue Inspection:** View live triage dashboard with risk filters and safety badges.
14. **Case Detail:** Open target case; inspect transcript, multimodal signals, and SVI drivers.
15. **Human Action:** Responder accepts or modifies recommendation with justification note.
16. **Audit Trail:** Inspect immutable audit log verifying complete human oversight provenance.
