from __future__ import annotations
import asyncio, uuid, json
from datetime import datetime
from pathlib  import Path
from typing   import AsyncGenerator
from fastapi  import (
    APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Request, WebSocket, WebSocketDisconnect, Depends,
)
from fastapi.responses import StreamingResponse, HTMLResponse
from loguru import logger
from core.models  import Framework
from core.state   import initial_state
from ingest.parser import parse_system_doc
from core.progress import subscribe as progress_subscribe

router   = APIRouter()
SESSIONS: dict[str, dict] = {}

NODE_PROGRESS = {
    "classify":              (20, "Classifying risk level..."),
    "detect_contradictions": (38, "Running ContradictionDetector..."),
    "map_obligations":       (55, "HyDE + Rerank retrieval..."),
    "analyze_gaps":          (82, "Building EvidenceChains (parallel)..."),
    "report":                (96, "Generating compliance dossier..."),
}

def get_graph(req: Request): return req.app.state.graph

def _v(x): return x.value if hasattr(x, "value") else x


@router.post("/analyze")
async def analyze(
    bg: BackgroundTasks, graph=Depends(get_graph),
    file: UploadFile = File(...),
    system_name: str = Form(default="Unknown System"),
    frameworks:  str = Form(default="eu_ai_act,gdpr,nist_ai_rmf"),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files accepted")

    fw_map  = {"eu_ai_act": Framework.EU_AI_ACT, "gdpr": Framework.GDPR, "nist_ai_rmf": Framework.NIST_AI_RMF}
    fw_list = [fw_map[f.strip()] for f in frameworks.split(",") if f.strip() in fw_map] or [Framework.EU_AI_ACT]

    sid = f"TMS-{uuid.uuid4().hex[:6].upper()}"
    pdf = Path("data/uploads") / f"{sid}.pdf"
    Path("data/uploads").mkdir(exist_ok=True)
    pdf.write_bytes(await file.read())

    SESSIONS[sid] = {
        "status": "pending", "system_name": system_name,
        "created_at": datetime.utcnow(),
        "current_node": None, "current_msg": None, "progress_pct": 0.0,
        "report": None, "error": None,
        "hitl_data": None, "hitl_event": asyncio.Event(), "hitl_response": None,
    }
    bg.add_task(_run_pipeline, sid, str(pdf), system_name, fw_list, graph)
    logger.info(f"[{sid}] Started — {file.filename}")
    return {"session_id": sid, "status": "pending", "estimated_minutes": 8}


async def _run_pipeline(sid, pdf_path, system_name, frameworks, graph):
    s = SESSIONS[sid]
    try:
        s["status"] = "running"; s["progress_pct"] = 5
        loop = asyncio.get_event_loop()
        text   = await loop.run_in_executor(None, parse_system_doc, pdf_path)
        state  = initial_state(session_id=sid, system_name=system_name,
                               system_text=text, frameworks=frameworks)
        config = {"configurable": {"thread_id": sid}}

        async for chunk in graph.astream(state, config, stream_mode="updates"):
            for node in chunk:
                if node in NODE_PROGRESS:
                    pct, msg = NODE_PROGRESS[node]
                    s["current_node"] = node; s["progress_pct"] = pct; s["current_msg"] = msg

            gs = graph.get_state(config)
            if gs.next and "hitl" in gs.next:
                interrupts = gs.tasks[0].interrupts if gs.tasks else []
                if interrupts:
                    s["status"] = "hitl_required"; s["hitl_data"] = interrupts[0]
                    try: await asyncio.wait_for(s["hitl_event"].wait(), timeout=1800)
                    except asyncio.TimeoutError:
                        s["status"] = "error"; s["error"] = "HITL timeout (30min)"; return
                    graph.update_state(config, values={"hitl_response": s["hitl_response"]}, as_node="hitl")
                    s["status"] = "running"; s["hitl_event"].clear()

        final = graph.get_state(config)
        if "report" in final.values and final.values["report"] is not None:
            s["report"] = final.values["report"]
            s["status"] = "completed"; s["progress_pct"] = 100
        else:
            s["status"] = "error"; s["error"] = "No report generated"

    except Exception as e:
        import traceback
        s["status"] = "error"; s["error"] = str(e)
        logger.error(sid + " " + str(e) + "\n" + traceback.format_exc())


@router.get("/sessions/{sid}")
async def get_session(sid: str):
    if sid not in SESSIONS: raise HTTPException(404)
    s = SESSIONS[sid]
    return {
        "session_id": sid, "status": s["status"],
        "system_name": s["system_name"],
        "current_node": s["current_node"], "current_msg": s["current_msg"],
        "progress_pct": s["progress_pct"], "error": s["error"],
        "created_at": s["created_at"].isoformat(),
        "hitl_required": s["status"] == "hitl_required",
    }


@router.get("/sessions/{sid}/report")
async def get_session_report(sid: str):
    if sid not in SESSIONS:
        raise HTTPException(404, "Session not found")
    s = SESSIONS[sid]
    if s["status"] != "completed":
        raise HTTPException(202, f"Not ready: {s['status']}")
    r = s["report"]
    if r is None:
        raise HTTPException(500, "Report is None despite completed status")
    return {
        "session_id": sid,
        "system_name": r.system_name,
        "compliance_score": r.compliance_score,
        "risk_classification": r.risk_classification.model_dump(),
        "gaps": [g.model_dump() for g in r.gaps],
        "contradictions": [c.model_dump() for c in r.contradictions],
        "critical_gaps": [g.model_dump() for g in r.critical_gaps],
        "frameworks_analyzed": [(_v(f) if hasattr(f, "value") else str(f)) for f in r.frameworks_analyzed],
        "evidence_integrity_ok": r.evidence_integrity_ok,
        "overall_confidence": r.overall_confidence,
        "generated_at": r.generated_at.isoformat(),
    }


@router.get("/sessions/{sid}/stream")
async def stream_session(sid: str):
    if sid not in SESSIONS: raise HTTPException(404)
    async def gen() -> AsyncGenerator[str, None]:
        while True:
            s = SESSIONS[sid]
            yield "data: " + json.dumps({
                "session_id": sid, "status": s["status"],
                "current_node": s["current_node"], "current_msg": s["current_msg"],
                "progress_pct": s["progress_pct"],
                "hitl_required": s["status"] == "hitl_required",
            }) + "\n\n"
            if s["status"] in ("completed", "error"): break
            await asyncio.sleep(2)
    return StreamingResponse(gen(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.websocket("/sessions/{sid}/hitl")
async def hitl_ws(ws: WebSocket, sid: str):
    await ws.accept()
    try:
        if sid not in SESSIONS:
            await ws.send_json({"type": "error", "message": "Session not found"}); return
        s = SESSIONS[sid]
        while s["status"] not in ("hitl_required", "completed", "error"):
            await ws.send_json({"type": "waiting", "progress_pct": s["progress_pct"]})
            await asyncio.sleep(3)
        if s["status"] == "hitl_required":
            await ws.send_json({"type": "review_required", "data": s["hitl_data"]})
            raw = await asyncio.wait_for(ws.receive_text(), timeout=1800)
            dec = json.loads(raw)
            s["hitl_response"] = dec; s["hitl_event"].set()
            await ws.send_json({"type": "resumed", "approved": dec.get("approved")})
    except (WebSocketDisconnect, asyncio.TimeoutError): pass


@router.get("/health")
async def health():
    return {
        "status": "healthy", "sessions_total": len(SESSIONS),
        "by_status": {st: sum(1 for v in SESSIONS.values() if v["status"] == st)
                      for st in ["pending", "running", "completed", "error", "hitl_required"]},
    }


@router.get("/progress/{job_id}")
async def progress_stream(job_id: str):
    return StreamingResponse(
        progress_subscribe(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )
