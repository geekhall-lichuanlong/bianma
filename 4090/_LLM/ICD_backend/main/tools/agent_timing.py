"""Measure actual model and trace stages on the server."""
from functools import wraps
from time import perf_counter
from uuid import uuid4


def _status(name, call_id, status, duration_ms=None):
    event = {
        "type": "agent_status", "agent_name": name, "call_id": call_id,
        "status": status, "status_text": f"{name}：{status}",
        "message": {"content": "", "reasoning_content": ""},
    }
    if duration_ms is not None:
        event["duration_ms"] = duration_ms
    return event


def timed_agent(function):
    @wraps(function)
    def wrapped(agent_name, *args, **kwargs):
        call_id = uuid4().hex
        yield _status(agent_name, call_id, "running")
        started = perf_counter()
        failed = False
        try:
            for event in function(agent_name, *args, **kwargs):
                # Replace the previous start-only events with one complete pair.
                if event.get("type") == "agent_status":
                    continue
                failed = failed or bool(event.get("error"))
                yield dict(event, call_id=call_id)
        except Exception:
            yield _status(agent_name, call_id, "failed", round((perf_counter() - started) * 1000, 3))
            raise
        else:
            yield _status(agent_name, call_id, "failed" if failed else "completed",
                          round((perf_counter() - started) * 1000, 3))
    return wrapped


def timed_call(name, function, *args, **kwargs):
    call_id = uuid4().hex
    yield _status(name, call_id, "running")
    started = perf_counter()
    try:
        result = function(*args, **kwargs)
    except Exception:
        yield _status(name, call_id, "failed", round((perf_counter() - started) * 1000, 3))
        raise
    yield _status(name, call_id, "completed", round((perf_counter() - started) * 1000, 3))
    return result
