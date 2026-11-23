import time
import uuid

class TelemetryMiddleware:
    """
    Pure ASGI middleware for request telemetry:
    - Injects/preserves X-Correlation-ID for end-to-end tracing.
    - Calculates execution duration and attaches X-Process-Time in milliseconds.
    - Operates purely at ASGI level without wrapping or buffering request streams,
      preventing streaming body/form-data hangs in FastAPI.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        correlation_id = None
        for name, value in scope.get("headers", []):
            if name.lower() == b"x-correlation-id":
                correlation_id = value.decode("latin1")
                break
        
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        start_time = time.perf_counter()

        async def send_with_telemetry_headers(message):
            if message["type"] == "http.response.start":
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                headers = list(message.get("headers", []))
                headers.append((b"x-correlation-id", correlation_id.encode("latin1")))
                headers.append((b"x-process-time", f"{duration_ms:.2f}ms".encode("latin1")))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_telemetry_headers)
