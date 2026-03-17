---
title: THEMIS
emoji: ⚖️
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: true
---

<div align="center">

<h1>THEMIS — EU AI Act Compliance Intelligence</h1>

<p><strong>The AI system that proves its own reasoning cannot be altered.</strong></p>

[![Live Demo](https://img.shields.io/badge/Live_Demo-themis--compliance.vercel.app-blue?style=for-the-badge)](https://themis-compliance.vercel.app)
[![API Docs](https://img.shields.io/badge/API_Docs-HuggingFace_Space-orange?style=for-the-badge)](https://achrafjarrou-themis.hf.space/docs)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge)](https://python.org)
[![EU AI Act](https://img.shields.io/badge/EU_AI_Act-Compliant-purple?style=for-the-badge)](https://eur-lex.europa.eu/)

</div>

---

## The Problem

Most AI compliance pipelines generate a report.

But between inference and output — there is a gap.

A gap where reasoning can be altered.
A gap where logs can be decoupled.
A gap where no one can prove what the system actually decided — and when.

**Regulators are asking: how do we know the reasoning wasn't touched after the fact?**

THEMIS is built to answer that question.

---

## How It Works

Upload any AI system documentation PDF.
THEMIS runs a **6-node LangGraph multi-agent pipeline** and produces a full EU AI Act compliance report — with cryptographic proof that the reasoning chain was never altered.
```
PDF → classify → detect_contradictions → map_obligations → analyze_gaps → [HITL] → report
```

Every compliance finding includes an **EvidenceChain** — a 4-step structured inference, SHA-256 sealed:
```
LEGAL_PREMISE  → Article 13 GDPR requires transparency       [conf: 95%]
DOCUMENT_FACT  → System processes 400,000 interactions/day   [conf: 80%]
INFERENCE      → Scale indicates high-risk data processing   [conf: 70%]
CONCLUSION     → DPIA required — not found in documentation  [conf: 85%]

SHA-256 → a3f8c2d1e9b74f6a...  ← tamper-proof seal
```

At report generation — every hash is re-verified.
If one step was altered after the fact → `integrity: false`

**The reasoning cannot be changed. Not by anyone.**

---

## Live Results

| AI System | Risk Level | Score | Critical Gaps | Chain Integrity |
|-----------|-----------|-------|---------------|-----------------|
| NEXUS FaceID (biometric surveillance) | 🔴 UNACCEPTABLE | 73/100 | 13 | ✅ VERIFIED |
| MediAssist AI (230 hospitals) | 🟡 LIMITED | 67/100 | 7 | ✅ VERIFIED |
| ContentStream Recommender | 🟢 MINIMAL | 69/100 | 2 | ✅ VERIFIED |

---

## Quick Start
```bash
# 1. Analyze a document
curl -X POST https://achrafjarrou-themis.hf.space/analyze \
  -F "file=@your_system.pdf" \
  -F "system_name=Your AI System" \
  -F "frameworks=EU AI Act"

# Returns: {"session_id": "TMS-XXXXXX"}

# 2. Stream progress (Server-Sent Events)
curl https://achrafjarrou-themis.hf.space/sessions/TMS-XXXXXX/stream

# 3. Get full report with EvidenceChain
curl https://achrafjarrou-themis.hf.space/sessions/TMS-XXXXXX/report
```

Test files included: `HighRisk_FacialRecognition.pdf` · `LimitedRisk_MedicalChatbot.pdf` · `MinimalRisk_Recommender.pdf`

---

## Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    THEMIS PIPELINE                          │
│                                                             │
│  PDF Upload                                                 │
│      │                                                      │
│  ┌───▼──────────┐   ┌──────────────┐   ┌────────────────┐  │
│  │   Classify   │──►│   Detect     │──►│  Map           │  │
│  │   Risk Level │   │Contradictions│   │  Obligations   │  │
│  └──────────────┘   └──────────────┘   └───────┬────────┘  │
│                                                 │           │
│                                         RAG: HyDE + RRF    │
│                                         96 EU AI Act arts  │
│                                                 │           │
│  ┌──────────────┐   ┌──────────────┐   ┌───────▼────────┐  │
│  │    Report    │◄──│  HITL Pause  │◄──│  Analyze Gaps  │  │
│  │  Generator   │   │  (if needed) │   │  EvidenceChain │  │
│  └──────┬───────┘   └──────────────┘   └────────────────┘  │
│         │                                                   │
│  SHA-256 re-verification on every hash                     │
│  integrity: true / false                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Detail |
|-------|-----------|--------|
| Orchestration | **LangGraph 0.2+** | 6 nodes, MemorySaver, HITL via `interrupt()` |
| LLM | **Groq llama-3.1-8b-instant** | JSON mode, structured outputs |
| RAG | **HyDE + RRF + Cross-Encoder** | Qdrant, 96 EU AI Act articles |
| Embeddings | **all-MiniLM-L6-v2** | dim=384, ms-marco reranker |
| Audit | **SHA-256 EvidenceChain** | 4-step typed inference, tamper-proof |
| API | **FastAPI async** | SSE streaming, WebSocket |
| Frontend | **React 18 + TypeScript** | Vite, Vercel |
| Deployment | **HuggingFace Spaces** | Docker, port 7860 |

---

## Why This Architecture

**The hard problem in AI compliance isn't generating the reasoning.**

It's proving the reasoning wasn't altered after the fact — in a way regulators can verify without trusting your infrastructure.

THEMIS solves this with a 4-step structured inference pipeline where each step is explicitly typed, confidence-weighted, and cryptographically sealed before the report is generated.

EU AI Act Articles 9, 13, and 17 require exactly this level of auditability for high-risk AI systems. THEMIS makes it automatic.

---

## Performance

| Metric | Result |
|--------|--------|
| Average report generation | ~2 minutes |
| RAG retrieval (96 articles) | HyDE + RRF + Cross-Encoder reranking |
| EvidenceChain integrity check | SHA-256 re-verification on all hashes |
| HITL escalation | Automatic on LOW confidence scores |

---

## Note on Cold Start

Running on HuggingFace free tier. If sleeping, the UI at [themis-compliance.vercel.app](https://themis-compliance.vercel.app) wakes it automatically — allow 30–60 seconds on first load.

---

## Built By

**Achraf Jarrou** — Systems Engineer (EQF Level 7)

[LinkedIn](https://linkedin.com/in/achraf-jarrou-4394bb342) · [GitHub](https://github.com/achrafjarrou) · Open to AI Engineer roles in EU (Amsterdam, Berlin) and Remote US/CA

Other projects: [AEGIS](https://github.com/achrafjarrou/aegis) (AI interviews) · [Orion](https://github.com/achrafjarrou/orion) (MCP orchestration) · [KAIROS](https://github.com/achrafjarrou/kairos) (multi-agent governance)

---

*Keywords: EU AI Act compliance, LangGraph multi-agent, RAG production, LLMOps, cryptographic audit trail, agentic AI, HITL, FastAPI, Python AI engineer, Amsterdam Berlin remote*
