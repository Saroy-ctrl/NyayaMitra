"""
sse.py — SSE event queue management for NyayaMitra.

Provides an in-memory asyncio.Queue per session_id.
The pipeline pushes events; the SSE endpoint consumes them.

Event payload shape:
  {
    "agent":  "intake" | "research" | "drafter" | "verifier" | "system",
    "status": "running" | "complete" | "error",
    "data":   { ...agent-specific metadata }
  }

Note: In-memory queues are sufficient for a single-process deployment (Railway).
For multi-process/multi-replica setups, replace with Redis pub/sub.
"""

import asyncio
import json
import logging
from typing import Any, AsyncGenerator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global event store — session_id -> asyncio.Queue of event dicts or None
# ---------------------------------------------------------------------------
pipeline_events: dict[str, asyncio.Queue] = {}

# Sentinel value — None pushed to signal the SSE stream should close
_SENTINEL = None

# Timeout in seconds before a stream is considered stale and closed
_STREAM_TIMEOUT = 300.0


def _get_or_create_queue(session_id: str) -> asyncio.Queue:
    """Return existing queue for session or create a new one."""
    if session_id not in pipeline_events:
        pipeline_events[session_id] = asyncio.Queue()
    return pipeline_events[session_id]


async def push_event(
    session_id: str,
    agent_name: str,
    status: str,
    data: dict[str, Any],
) -> None:
    """
    Enqueue an SSE event for a session.

    Creates the queue if it does not yet exist (safe to call before
    create_sse_generator).

    Args:
        session_id: Identifies the pipeline run.
        agent_name: Which agent is emitting the event.
        status:     "running" | "complete" | "error".
        data:       Arbitrary metadata dict.
    """
    queue = _get_or_create_queue(session_id)
    event = {"agent": agent_name, "status": status, "data": data}
    logger.debug("SSE push [%s] %s/%s", session_id[:8], agent_name, status)
    await queue.put(event)


async def close_stream(session_id: str) -> None:
    """Signal the SSE endpoint to close the connection for this session."""
    queue = _get_or_create_queue(session_id)
    await queue.put(_SENTINEL)


async def create_sse_generator(session_id: str) -> AsyncGenerator[dict, None]:
    """
    Async generator consumed by sse-starlette's EventSourceResponse.

    Creates a queue for the session if one does not exist yet, then yields
    SSE-formatted dicts until the None sentinel is received or a 300-second
    timeout occurs.

    Args:
        session_id: The pipeline session to stream events for.

    Yields:
        Dicts of the shape {"data": "<json-string>"} that sse-starlette
        wraps into SSE frames on the wire.
    """
    queue = _get_or_create_queue(session_id)

    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=_STREAM_TIMEOUT)
            except asyncio.TimeoutError:
                logger.warning("SSE stream timeout for session %s", session_id[:8])
                yield {
                    "data": json.dumps(
                        {
                            "agent": "system",
                            "status": "error",
                            "data": {"error": "Stream timeout after 300 seconds"},
                        },
                        ensure_ascii=False,
                    )
                }
                break

            # None sentinel signals end of stream
            if event is _SENTINEL:
                break

            yield {"data": json.dumps(event, ensure_ascii=False)}

    finally:
        cleanup_session(session_id)


def cleanup_session(session_id: str) -> None:
    """Remove the event queue for a completed or timed-out session."""
    removed = pipeline_events.pop(session_id, None)
    if removed is not None:
        logger.debug("SSE cleanup: session %s removed", session_id[:8])
