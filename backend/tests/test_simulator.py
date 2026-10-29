"""
What-If Simulator and Monotonicity Sanity Tests.
"""

def test_simulator_monotonicity_sanity(client_teacher):
    # Base simulation
    resp1 = client_teacher.post(
        "/api/v1/simulator/what-if",
        json={"student_id": "STU101", "overrides": {"attendance_pct": 54.0}},
    )
    assert resp1.status_code == 200
    p_high_1 = resp1.json()["simulated"]["probabilities"]["high"]

    # Improvement simulation (raise attendance to 95)
    resp2 = client_teacher.post(
        "/api/v1/simulator/what-if",
        json={"student_id": "STU101", "overrides": {"attendance_pct": 95.0}},
    )
    assert resp2.status_code == 200
    p_high_2 = resp2.json()["simulated"]["probabilities"]["high"]

    # Monotonicity check: improving attendance must not increase high risk probability
    assert p_high_2 <= p_high_1 + 1e-4


def test_simulator_bounds_validation(client_teacher):
    # Invalid attendance (150%) must return 422 with readable string detail
    resp = client_teacher.post(
        "/api/v1/simulator/what-if",
        json={"student_id": "STU101", "overrides": {"attendance_pct": 150.0}},
    )
    assert resp.status_code == 422
    assert "detail" in resp.json()
    assert isinstance(resp.json()["detail"], str)
