"""
Authentication and Role-Based Access Control (RBAC) Matrix Tests.
"""

from datetime import timedelta
import pytest
from app.core.security import create_access_token


def test_login_success(client):
    resp = client.post("/api/v1/auth/login", json={"username": "teacher", "password": "vit2026"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "TEACHER"


def test_login_invalid_password(client):
    resp = client.post("/api/v1/auth/login", json={"username": "teacher", "password": "wrongpassword"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid username or password."


def test_login_throttling(client):
    username = "throttle_user"
    for i in range(5):
        resp = client.post("/api/v1/auth/login", json={"username": username, "password": "bad"})
        assert resp.status_code == 401

    # 6th attempt must be 429 Throttled
    resp6 = client.post("/api/v1/auth/login", json={"username": username, "password": "bad"})
    assert resp6.status_code == 429
    assert "too many" in resp6.json()["detail"].lower()


def test_expired_jwt(client):
    # Expired token in the past
    expired_token = create_access_token(
        subject="teacher",
        role="TEACHER",
        expires_delta=timedelta(minutes=-10),
    )
    client.headers["Authorization"] = f"Bearer {expired_token}"
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()


def test_rbac_student_roster_forbidden_for_student(client_student):
    resp = client_student.get("/api/v1/students")
    assert resp.status_code == 403


def test_rbac_student_roster_allowed_for_teacher(client_teacher):
    resp = client_teacher.get("/api/v1/students")
    assert resp.status_code == 200


def test_student_can_read_own_data(client_student):
    # STU101 is linked to student user
    resp = client_student.get("/api/v1/students/STU101")
    assert resp.status_code == 200
    assert resp.json()["id"] == "STU101"


def test_student_cannot_read_peer_data(client_student):
    # STU102 belongs to peer
    resp = client_student.get("/api/v1/students/STU102")
    assert resp.status_code == 403
