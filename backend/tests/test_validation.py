"""
Contract Validation, Feature Consistency, Data Entry, and Import Tests.
"""

import json
from pathlib import Path
from app.services.feature_service import compute_features_for_student_semester
from app.core.config import PROJECT_ROOT


def test_feature_derivation_consistency(db_session):
    """
    Mandatory Section 7 consistency test:
    STU101 seeded with: attendance=54, quiz=46, midsem=14, practical=16, backlogs=2.
    Assert each derived core feature is within 1.0 of target.
    """
    from app.models.student import Student
    from sqlalchemy import select

    student = db_session.scalar(select(Student).where(Student.student_code == "STU101"))
    feats = compute_features_for_student_semester(db_session, student.id, semester_code="sem5")

    assert abs(feats["attendance_pct"] - 54.0) <= 1.0
    assert abs(feats["quiz_avg"] - 46.0) <= 1.0
    assert abs(feats["internal_marks"] - 14.0) <= 1.0
    assert abs(feats["practical_marks"] - 16.0) <= 1.0
    assert abs(feats["backlogs"] - 2.0) <= 1.0


def test_validation_error_returns_string_detail(client):
    # Assessment score > max must return 422 with string detail
    token = client.post("/api/v1/auth/login", json={"username": "teacher", "password": "vit2026"}).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    resp = client.post(
        "/api/v1/assessments",
        json={"student_id": "STU101", "subject": "CS301", "assessment": "Quiz 1", "score": 150.0, "max": 100.0},
    )
    assert resp.status_code == 422
    data = resp.json()
    assert "detail" in data
    assert isinstance(data["detail"], str)
    assert "cannot exceed" in data["detail"].lower() or "score" in data["detail"].lower()


def test_import_with_bad_row(client_teacher):
    # Batch containing 1 good row and 1 invalid row
    payload = {
        "records": [
            {"roll": "221101", "name": "Aditya", "division": "SEDA-A", "attendance": 75, "quiz": 65, "assignment": 80, "backlogs": 0},
            {"roll": "221199", "name": "Bad Student", "division": "SEDA-A", "attendance": 150, "quiz": 65, "assignment": 80, "backlogs": 0},  # Invalid att
        ],
        "semester": "sem5",
    }
    resp = client_teacher.post("/api/v1/imports", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["rows_total"] == 2
    assert data["rows_ok"] == 1
    assert data["rows_failed"] == 1
    assert len(data["errors"]) == 1
    assert data["errors"][0]["row"] == 2


def test_data_writes_update_prediction(client_teacher, db_session):
    from app.models.student import Student
    from app.models.prediction import Prediction
    from sqlalchemy import select

    student = db_session.scalar(select(Student).where(Student.student_code == "STU101"))

    # Initial score
    resp1 = client_teacher.get("/api/v1/predictions/STU101?semester=sem5")
    assert resp1.status_code == 200

    # Write a new attendance record
    write_resp = client_teacher.post(
        "/api/v1/attendance",
        json={"student_id": "STU101", "subject": "CS301", "date": "2026-10-28", "attendance_pct": 98.0},
    )
    assert write_resp.status_code == 200
    new_risk = write_resp.json()["prediction"]["risk_level"]

    # Verify predictions table updated
    latest_pred = db_session.scalar(
        select(Prediction)
        .where(
            Prediction.student_id == student.id,
            Prediction.semester_code == "sem5",
            Prediction.is_latest == True,
        )
    )
    assert latest_pred is not None
    assert latest_pred.risk_level == new_risk


def test_api_contract_conformance(client_teacher):
    contract_file = PROJECT_ROOT / "docs" / "api_contract.json"
    assert contract_file.exists(), "Missing docs/api_contract.json"
    with open(contract_file, "r", encoding="utf-8") as f:
        contract = json.load(f)["endpoints"]

    # Test GET /api/v1/health
    resp = client_teacher.get("/api/v1/health")
    for key in contract["GET /api/v1/health"]["required_keys"]:
        assert key in resp.json()

    # Test GET /api/v1/students
    resp = client_teacher.get("/api/v1/students")
    for key in contract["GET /api/v1/students"]["required_keys"]:
        assert key in resp.json()

    # Test GET /api/v1/students/STU101
    resp = client_teacher.get("/api/v1/students/STU101")
    for key in contract["GET /api/v1/students/{id}"]["required_keys"]:
        assert key in resp.json()
