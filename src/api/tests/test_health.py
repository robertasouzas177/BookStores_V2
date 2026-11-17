"""test_health.py — Testes das sondas de saúde (liveness e readiness).

Casos de teste:
- HEALTH-001: GET /health/live → 200 {"status": "UP"}
- HEALTH-002: GET /health/ready → 200 com checks.database.status = "UP"
"""

from fastapi.testclient import TestClient


LIVE_URL = "/health/live"
READY_URL = "/health/ready"


# ---------------------------------------------------------------------------
# HEALTH-001 — Liveness probe
# ---------------------------------------------------------------------------


def test_health001_liveness(client: TestClient) -> None:
    """HEALTH-001: GET /health/live → 200 com status UP."""
    response = client.get(LIVE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "UP"


# ---------------------------------------------------------------------------
# HEALTH-002 — Readiness probe
# ---------------------------------------------------------------------------


def test_health002_readiness(client: TestClient) -> None:
    """HEALTH-002: GET /health/ready → 200 com checks.database.status UP."""
    response = client.get(READY_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "UP"
    assert "checks" in body
    assert "database" in body["checks"]
    assert body["checks"]["database"]["status"] == "UP"
