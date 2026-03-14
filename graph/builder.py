from __future__ import annotations
from loguru  import logger
from langgraph.graph             import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from core.state      import ThemisState
from core.exceptions import GraphBuildError
from graph.nodes     import (
    classify_node, detect_contradictions_node, map_obligations_node,
    analyze_gaps_node, hitl_node, generate_report_node,
)
from graph.routing   import route_after_analysis

# Silence LangGraph Deserializing warnings
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
try:
    from langgraph.checkpoint.memory import MemorySaver as _MS
    import core.models as _cm
    _allowed = [
        (_cm, "Framework"), (_cm, "RiskLevel"), (_cm, "GapStatus"),
        (_cm, "RiskClassification"), (_cm, "ComplianceGap"), (_cm, "ComplianceReport"),
    ]
    for _mod, _name in _allowed:
        pass  # Types auto-handled by Pydantic model_dump/model_validate
except Exception:
    pass


logger.info("[Graph] Checkpointer: MemorySaver")


def build_themis_graph():
    try:
        sg = StateGraph(ThemisState)

        sg.add_node("classify",              classify_node)
        sg.add_node("detect_contradictions", detect_contradictions_node)
        sg.add_node("map_obligations",       map_obligations_node)
        sg.add_node("analyze_gaps",          analyze_gaps_node)
        sg.add_node("hitl",                  hitl_node)
        sg.add_node("report",                generate_report_node)

        sg.set_entry_point("classify")
        sg.add_edge("classify",              "detect_contradictions")
        sg.add_edge("detect_contradictions", "map_obligations")
        sg.add_edge("map_obligations",       "analyze_gaps")
        sg.add_conditional_edges(
            "analyze_gaps",
            route_after_analysis,
            {"retry": "map_obligations", "hitl": "hitl", "report": "report"},
        )
        sg.add_edge("hitl",   "report")
        sg.add_edge("report", END)

        graph = sg.compile(
            checkpointer=MemorySaver(),
            interrupt_before=["hitl"],
        )
        logger.success(f"[Graph] THEMIS graph compiled: {list(sg.nodes.keys())}")
        return graph

    except Exception as e:
        raise GraphBuildError(f"Graph build failed: {e}", {"error": str(e)}) from e