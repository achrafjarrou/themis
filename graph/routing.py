from __future__ import annotations
from typing  import Literal
from loguru  import logger
from core.state  import ThemisState
from core.models import GapStatus

MAX_RETRIES = 2
CONF_RETRY  = 0.70   # retry if confidence < this
CONF_HITL   = 0.60   # escalate to human if confidence < this
CRIT_HITL   = 0       # escalate if more than this many critical missing gaps



def route_after_analysis(state: ThemisState) -> Literal["retry", "hitl", "report"]:
    conf          = state["overall_confidence"]
    retry_count   = state["retry_count"]
    critical_miss = sum(
        1 for g in state["gaps"]
        if g.status == GapStatus.MISSING and g.severity >= 4
    )

    # Path 1: retry — low confidence, haven't exceeded max retries
    if conf < CONF_RETRY and retry_count < MAX_RETRIES:
        logger.warning(f"Route: retry ({retry_count+1}/{MAX_RETRIES}) conf={conf:.2f}")
        return "retry"

    # Path 2: HITL — dangerously low confidence OR too many critical gaps
    if conf < CONF_HITL or critical_miss > CRIT_HITL:
        logger.warning(f"Route: HITL conf={conf:.2f} critical_missing={critical_miss}")
        return "hitl"

    # Path 3: report — confidence acceptable
    logger.info(f"Route: report conf={conf:.2f} critical_missing={critical_miss}")
    return "report"

