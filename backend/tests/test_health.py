import pytest

def test_healthz_endpoint(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "predictive-maintenance-api"

def test_readyz_endpoint(client):
    response = client.get("/readyz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"

def test_telemetry_headers(client):
    response = client.get("/healthz", headers={"X-Correlation-ID": "custom-trace-12345"})
    assert response.status_code == 200
    # Custom correlation ID is preserved
    assert response.headers.get("X-Correlation-ID") == "custom-trace-12345"
    # Latency header is present
    assert "X-Process-Time" in response.headers
    assert response.headers["X-Process-Time"].endswith("ms")

def test_generated_correlation_id(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    # Auto-generated UUID is present
    corr_id = response.headers.get("X-Correlation-ID")
    assert corr_id is not None
    assert len(corr_id) > 10
