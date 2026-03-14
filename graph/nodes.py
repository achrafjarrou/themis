# THEMIS — graph\nodes.py

from __future__ import annotations
import asyncio
from loguru import logger
from langgraph.types import interrupt

from core.state   import ThemisState
from agents.classifier    import classify_system_risk
from agents.contradiction import detect_contradictions
from agents.analyzer      import analyze_all_articles
from agents.reporter      import generate_report
from rag.reranker         import retrieve_and_rerank


async def classify_node(state: ThemisState) -> dict:
    logger.info(f"[{state['session_id']}] Node: classify")
    rc = await classify_system_risk(state["system_text"], state["system_name"])
    return {"risk_classification": rc}


async def detect_contradictions_node(state: ThemisState) -> dict:
    logger.info(f"[{state['session_id']}] Node: detect_contradictions")
    contradictions = await detect_contradictions(state["system_text"])
    if contradictions:
        logger.warning(f"ContradictionDetector™: {len(contradictions)} found")
    return {"contradictions": contradictions}


async def map_obligations_node(state: ThemisState) -> dict:
    logger.info(f"[{state['session_id']}] Node: map_obligations")
    tasks = [
        retrieve_and_rerank(
            f"compliance obligations for {fw.value if hasattr(fw,'value') else str(fw)} AI system",
            framework=fw.value if hasattr(fw,"value") else str(fw),
            top_k_post=8,
        )
        for fw in state["frameworks"]
    ]
    results = await asyncio.gather(*tasks)
    articles = [doc for batch in results for doc in batch]
    logger.info(f"Retrieved {len(articles)} relevant articles")
    return {"retrieved_articles": articles}


async def analyze_gaps_node(state: ThemisState) -> dict:
    logger.info(f"[{state['session_id']}] Node: analyze_gaps")
    gaps, confidence = await analyze_all_articles(
        system_text=state["system_text"],
        articles=state["retrieved_articles"],
        risk_level=state["risk_classification"].risk_level,
    )
    return {"gaps": gaps, "overall_confidence": confidence}



async def hitl_node(state: ThemisState) -> dict:
    """
    Human-in-the-loop node — uses LangGraph interrupt() to pause execution.
    The API's WebSocket endpoint delivers the gaps to the reviewer
    and passes back the approval via graph.update_state().
    """
    logger.warning(f"[{state['session_id']}] HITL triggered — awaiting human review")
    decision = interrupt({
        "reason": "Low confidence or critical gaps require human review",
        "gaps_to_review": [g.model_dump() for g in state["gaps"][:5]],
        "confidence": state["overall_confidence"],
    })
    logger.info(f"[{state['session_id']}] HITL decision received: {decision}")
    return {"hitl_response": decision}



async def generate_report_node(state: ThemisState) -> dict:
    logger.info(f"[{state['session_id']}] Node: generate_report")
    report = await generate_report(state)
    logger.success(f"Report generated: score={report.compliance_score:.1f} integrity={report.evidence_integrity_ok}")
    return {"report": report}


# wrapper supprime — recursion infinie corrigee