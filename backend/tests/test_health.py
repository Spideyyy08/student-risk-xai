"""
Health Check and Public Readiness Endpoint Tests.
"""

def test_health_endpoint(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["db"] == "ok"
    assert "model_loaded" in data


def test_top_level_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "model_loaded" in data
