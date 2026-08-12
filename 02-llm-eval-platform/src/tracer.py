import os
import json
from functools import wraps
from datetime import datetime


class TraceSpan:
    def __init__(self, name: str, trace_id: str):
        self.name = name
        self.trace_id = trace_id
        self.start = datetime.utcnow()
        self.end = None
        self.status = "pending"
        self.error = None

    def close(self, status: str = "success", error: str = None):
        self.end = datetime.utcnow()
        self.status = status
        self.error = error

    @property
    def duration_s(self) -> float:
        e = self.end or datetime.utcnow()
        return (e - self.start).total_seconds()

    def dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "name": self.name,
            "duration_s": round(self.duration_s, 3),
            "status": self.status,
            "error": self.error,
            "start": self.start.isoformat(),
            "end": self.end.isoformat() if self.end else None,
        }


class Tracer:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.traces: list[dict] = []

    def trace(self, name: str):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.enabled:
                    return await func(*args, **kwargs)

                trace_id = f"tr_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{id(func)}"
                span = TraceSpan(name, trace_id)

                try:
                    result = await func(*args, **kwargs)
                    span.close("success")
                    return result
                except Exception as e:
                    span.close("error", str(e))
                    raise
                finally:
                    self.traces.append(span.dict())

            return wrapper
        return decorator

    def trace_sync(self, name: str):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                trace_id = f"tr_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{id(func)}"
                span = TraceSpan(name, trace_id)

                try:
                    result = func(*args, **kwargs)
                    span.close("success")
                    return result
                except Exception as e:
                    span.close("error", str(e))
                    raise
                finally:
                    self.traces.append(span.dict())

            return wrapper
        return decorator

    def flush(self) -> list[dict]:
        traces = self.traces.copy()
        self.traces.clear()
        return traces


tracer = Tracer()
