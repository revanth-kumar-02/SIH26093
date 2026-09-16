# SIH26093 — Privacy, Ethics, and Data Minimization

## 1. Informed Consent Protocol
Prior to any audio recording or narrative intake, victims are presented with clear, accessible disclosures:
- Transparent notification that AI assists in organizing information for human responders.
- Affirmation that AI does not replace human counselors or responders.
- Clear assurance of confidentiality and right to exit or request human transfer at any moment.

## 2. Data Minimization & Retention
- **Audio Files:** Temporary in-memory or ephemeral processing; raw audio is not persisted long-term in the database.
- **Identifiable Data:** Pseudonymous intake; sessions are linked via UUIDs rather than personal identity documents.
- **Audit Logs:** Immutable audit events record operational provenance without duplicating sensitive victim narratives.

## 3. Preservation of Uncertainty
The system strictly adheres to the principle that **missing information does not equal absence of risk**. Whenever modalities are absent, corrupted, or inconclusive, the SVI engine assigns uncertainty penalties and explicitly highlights information gaps to the responder.
