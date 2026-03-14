from __future__ import annotations
import os, functools, time
from typing  import Callable, Any
from loguru  import logger

# Langfuse — optional, gracefully disabled if not configured
try:
    from langfuse import Langfuse
    _lf = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "local"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY", "local"),
        host=os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
    )
    LANGFUSE_ENABLED = True
    logger.info("Langfuse tracing enabled")
except Exception:
    _lf = None
    LANGFUSE_ENABLED = False
    logger.warning("Langfuse not available — tracing disabled (install langfuse to enable)")


def trace_node(node_name: str):
    """
    Decorator for LangGraph nodes — logs execution time and traces to Langfuse.
    Usage: @trace_node("classify")
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            sid   = args[0].get("session_id", "?") if args else "?"

            span = None
            if LANGFUSE_ENABLED and _lf:
                try:
                    span = _lf.start_span(name=node_name, metadata={"session_id": sid})
                except Exception: pass

            try:
                result = await fn(*args, **kwargs)
                elapsed = (time.perf_counter() - start) * 1000
                logger.debug(f"[{sid}] {node_name} completed in {elapsed:.0f}ms")
                if span:
                    span.end(output={"status": "ok", "ms": elapsed})
                return result
            except Exception as e:
                if span:
                    span.end(output={"status": "error", "error": str(e)})
                raise
        return wrapper
    return decorator
