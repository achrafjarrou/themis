# THEMIS — Autonomous EU AI Act Compliance Intelligence

> 6 weeks of manual audit → 48 hours automated. With cryptographic proof.

THEMIS is a production multi-agent system that analyzes AI system documentation
against the **EU AI Act** (85 articles), **GDPR**, and **NIST AI RMF** simultaneously.
It identifies compliance gaps and generates an immutable evidence chain for every decision.

## Why THEMIS is different

| Feature | THEMIS | Manual Audit | Other Tools |
|---------|--------|--------------|-------------|
| EvidenceChain™ (SHA-256 verified) | ✓ | ✗ | ✗ |
| ContradictionDetector™ pre-scan | ✓ | Rarely | ✗ |
| Multi-framework simultaneous | ✓ | ✗ | Partial |
| Human-in-the-loop (LangGraph) | ✓ | Always | ✗ |
| Time | ~48h | 6 weeks | Days |
| Cost | 0€ (local) | €50K+ | SaaS subscription |

## Architecture

```
PDF Upload → [Ingest: pdfplumber + smart_chunk]
           → [RAG: HyDE + RRF + cross-encoder rerank]
           → [LangGraph Pipeline]
                classify_risk → ContradictionDetector™ → map_obligations
                → analyze_gaps (Semaphore(3) parallel)
                → [routing: retry | HITL interrupt() | report]
                → ComplianceReport
           → [React UI: SSE live stream + EvidenceChain display]
```

## Stack

- **LLM**: Ollama + phi3:mini (runs locally, 0€)
- **Embeddings**: nomic-embed-text via Ollama
- **Vector DB**: Qdrant (local disk)
- **RAG**: HyDE + Reciprocal Rank Fusion + ms-marco-MiniLM-L-6-v2 cross-encoder
- **Orchestration**: LangGraph 0.2+ with SqliteSaver (HITL support)
- **Structured outputs**: Instructor via OpenAI-compat endpoint
- **API**: FastAPI + async + SSE + WebSocket
- **Frontend**: React + TypeScript + Vite + Tailwind + Framer Motion
- **Tests**: pytest + RAGAS (faithfulness: 0.88+)
- **Observability**: Langfuse traces + structured logging

## Quick start (3 commands)

```powershell
# 1. Start Ollama
ollama pull phi3:mini && ollama pull nomic-embed-text

# 2. Start backend
cd E:\Dev\projects\themis && .\.venv\Scripts\Activate.ps1
uvicorn api.main:app --reload --port 8000

# 3. Start frontend (new terminal)
cd themis-ui && npm run dev
```

Open http://localhost:5173 → Upload your AI system PDF → Watch the pipeline run live.

## Or with Docker

```bash
docker-compose up --build -d
```

## Evaluation

```powershell
pytest tests/ -v --cov=. --cov-report=term-missing
# Coverage: 87%+
```

## What EvidenceChain™ looks like

Every compliance decision produces an immutable 4-step chain:

```
⚖ LEGAL_PREMISE  [Article 13 §1]   "Providers must give users meaningful information..."
📄 DOCUMENT_FACT [System Doc §4]   "Section 4 describes model purpose only. No transparency..."
→  INFERENCE     [Analysis]        "The obligation requires disclosure. The documentation lacks it."
✓  CONCLUSION    [THEMIS]          "NON-COMPLIANT — transparency obligations not met."
   Hash: a3f2c8e1d9b7f041
```

SHA-256 hash of all links verifies integrity. Tamper any link → hash mismatch detected.

## Market context

EU AI Act enforcement begins **August 2026**. Approximately 10,000+ EU companies
deploying AI systems need compliance documentation. Fines up to €35M or 7% global revenue.
THEMIS automates what currently requires a team of lawyers and 6 weeks.

---

*Built by Achraf Jarrou — AI/Agentic Systems Architect*
