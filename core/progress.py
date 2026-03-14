"""core/progress.py — Lightweight in-process SSE event store"""
import asyncio
import json
import time
from collections import defaultdict
from typing import AsyncGenerator

# job_id -> list of queues listening
_queues: dict[str, list[asyncio.Queue]] = defaultdict(list)

# job_id -> last known state (for late subscribers)
_snapshots: dict[str, dict] = {}


def emit(job_id: str, event: dict) -> None:
    """Thread-safe emit from any async context."""
    event.setdefault("ts", time.time())
    _snapshots[job_id] = event
    for q in _queues[job_id]:
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            pass


async def subscribe(job_id: str) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted strings until 'done' event."""
    q: asyncio.Queue = asyncio.Queue(maxsize=50)
    _queues[job_id].append(q)

    # Replay last snapshot immediately so the client sees current state
    if job_id in _snapshots:
        snap = _snapshots[job_id]
        yield f"data: {json.dumps(snap)}\n\n"

    try:
        while True:
            event = await asyncio.wait_for(q.get(), timeout=30)
            yield f"data: {json.dumps(event)}\n\n"
            if event.get("type") == "done":
                break
    except asyncio.TimeoutError:
        yield 'data: {"type":"heartbeat"}\n\n'
    finally:
        _queues[job_id].discard(q) if hasattr(_queues[job_id], 'discard') else None
        try:
            _queues[job_id].remove(q)
        except ValueError:
            pass
