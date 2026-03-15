﻿---
title: THEMIS
emoji: ⚖️
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: true
---

<div align="center">

# THEMIS - Autonomous EU AI Act Compliance Intelligence

**Upload an AI system PDF. Get a full compliance report in 2 minutes. With cryptographic proof.**

[Live UI - themis-compliance.vercel.app](https://themis-compliance.vercel.app) | [API Docs](https://achrafjarrou-themis.hf.space/docs)

</div>

---

## Try it now

1. Go to **[themis-compliance.vercel.app](https://themis-compliance.vercel.app)**
2. Upload any AI system documentation PDF
3. Get a full EU AI Act + GDPR + NIST AI RMF compliance report

**Test files ready to use:**
- `HighRisk_FacialRecognition.pdf` — biometric surveillance, expect UNACCEPTABLE risk
- `LimitedRisk_MedicalChatbot.pdf` — 230 hospitals, expect LIMITED + DPIA gaps
- `MinimalRisk_Recommender.pdf` — well-documented, expect MINIMAL risk

---

## What THEMIS does

THEMIS is a **6-node LangGraph multi-agent pipeline** that automates EU AI Act compliance auditing:
```
PDF -> classify -> detect_contradictions -> map_obligations (RAG) -> analyze_gaps -> [HITL?] -> report
```

Each compliance gap includes an **EvidenceChain(TM)** — a 4-step reasoning chain:
```
LEGAL_PREMISE  ->  Article 13 GDPR (confidence: 95%)
DOCUMENT_FACT  ->  "System handles 400,000 interactions/day" (80%)
INFERENCE      ->  "Scale indicates high-risk processing" (70%)
CONCLUSION     ->  "DPIA required — not found in documentation" (85%)
SHA-256 Hash   ->  a3f8c2d1e9b74f6a  (tamper-proof)
```

---

## API Usage
```bash
# 1. Analyze a document
curl -X POST https://achrafjarrou-themis.hf.space/analyze \
  -F "file=@your_system.pdf" \
  -F "system_name=Your AI System" \
  -F "frameworks=EU AI Act" \
  -F "frameworks=GDPR"

# Returns: {"session_id": "TMS-XXXXXX"}

# 2. Stream progress (Server-Sent Events)
curl https://achrafjarrou-themis.hf.space/sessions/TMS-XXXXXX/stream

# 3. Get full report
curl https://achrafjarrou-themis.hf.space/sessions/TMS-XXXXXX/report

# 4. Health check
curl https://achrafjarrou-themis.hf.space/health
```

---

## Live Results

| System | Risk | Score | Critical Gaps |
|---|---|---|---|
| NEXUS FaceID (biometric surveillance) | UNACCEPTABLE | 73/100 | 13 |
| MediAssist AI (230 hospitals) | LIMITED | 67/100 | 7 |
| ContentStream Recommender | MINIMAL | 69/100 | 2 |

EvidenceChain(TM) integrity: verified on all reports

---

## Tech Stack

| Layer | Stack |
|---|---|
| Orchestration | LangGraph 0.2+ (6 nodes, MemorySaver, HITL via interrupt()) |
| LLM | Groq llama-3.1-8b-instant (JSON mode) |
| RAG | HyDE + RRF + Cross-Encoder (Qdrant, 96 EU AI Act articles) |
| Embeddings | all-MiniLM-L6-v2 (dim=384) + ms-marco-MiniLM reranker |
| API | FastAPI (async, SSE, WebSocket) |
| Frontend | React 18 + TypeScript + Vite (Vercel) |

---

## Cold start note

This Space runs on HuggingFace free tier. If sleeping, the UI at [themis-compliance.vercel.app](https://themis-compliance.vercel.app) wakes it up automatically — allow 30-60 seconds on first load.

---

THEMIS v1.0.0 | Built by Achraf Jarrou (https://linkedin.com/in/achrafjarrou) | EU AI Act enforcement Aug 2026