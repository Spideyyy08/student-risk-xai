"""
Smoke Test Suite.
Exercises all frozen frontend API endpoints using httpx against http://127.0.0.1:8000.
ASCII output, exit code 1 on failure.
"""

import sys
import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"


def run_smoke_tests():
    print("==========================================================")
    print("RUNNING BACKEND SMOKE TESTS AGAINST", BASE_URL)
    print("==========================================================")

    client = httpx.Client(base_url=BASE_URL, timeout=10.0)
    passed = 0
    failed = 0
    total = 0

    def test_case(name: str, method: str, path: str, **kwargs):
        nonlocal passed, failed, total
        total += 1
        try:
            resp = client.request(method, path, **kwargs)
            if resp.status_code in [200, 201]:
                print(f"[PASS] {method:4s} {path:<45} (Status: {resp.status_code})")
                passed += 1
                return resp
            else:
                print(f"[FAIL] {method:4s} {path:<45} (Status: {resp.status_code}) - {resp.text[:100]}")
                failed += 1
                return resp
        except Exception as err:
            print(f"[FAIL] {method:4s} {path:<45} (Exception: {err})")
            failed += 1
            return None

    # 1. Health check (no auth)
    test_case("Health Check", "GET", "/health")

    # 2. Login as Teacher
    login_resp = test_case(
        "Teacher Login",
        "POST",
        "/auth/login",
        json={"username": "teacher", "password": "vit2026"},
    )
    if not login_resp or login_resp.status_code != 200:
        print("[FATAL] Teacher login failed. Halting remaining smoke tests.")
        sys.exit(1)

    token = login_resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    # 3. Auth Me
    test_case("Current User Profile", "GET", "/auth/me")

    # 4. Class Summary (All & SEDA-A)
    test_case("Class Summary (ALL)", "GET", "/analytics/class-summary?division=ALL&semester=sem5")
    test_case("Class Summary (SEDA-A)", "GET", "/analytics/class-summary?division=SEDA-A&semester=sem5")

    # 5. Students Roster List
    test_case("Students List (Full)", "GET", "/students?division=ALL&semester=sem5&page_size=200")
    test_case("Students Filtered (High Risk)", "GET", "/students?risk=HIGH&semester=sem5")

    # 6. Student Profile Detail
    test_case("Student Detail (STU101)", "GET", "/students/STU101?semester=sem5")
    test_case("Student Detail by Roll (221101)", "GET", "/students/221101?semester=sem5")

    # 7. Predictions & Explanations
    test_case("Student Prediction", "GET", "/predictions/STU101?semester=sem5")
    test_case("Student SHAP Explanation", "GET", "/explanations/STU101?semester=sem5&top=6")

    # 8. Subject Breakdown & Trends
    test_case("Subject Breakdown", "GET", "/analytics/STU101/subjects?semester=sem5")
    test_case("Longitudinal Trends", "GET", "/analytics/STU101/trends?semester=sem5")

    # 9. Recommendations
    test_case("Recommendations List", "GET", "/recommendations/STU101?semester=sem5")

    # 10. Simulator What-If
    test_case(
        "What-If Simulator",
        "POST",
        "/simulator/what-if",
        json={"student_id": "STU101", "overrides": {"attendance_pct": 85.0, "backlogs": 0}},
    )

    # 11. Interventions (Get & Post)
    test_case("Interventions List", "GET", "/interventions?student_id=STU101")
    test_case(
        "Log Intervention",
        "POST",
        "/interventions",
        json={
            "student_id": "STU101",
            "type": "Counselling",
            "status": "Planned",
            "date": "2026-10-29",
            "notes": "Automated smoke test intervention verification.",
        },
    )

    # 12. Data Entry Writes
    test_case(
        "Log Attendance Snapshot",
        "POST",
        "/attendance",
        json={"student_id": "STU101", "subject": "CS301", "date": "2026-10-28", "attendance_pct": 72.0},
    )
    test_case(
        "Log Assessment Score",
        "POST",
        "/assessments",
        json={"student_id": "STU101", "subject": "CS301", "assessment": "Quiz 2", "score": 80.0, "max": 100.0},
    )
    test_case(
        "Log Assignment Submission",
        "POST",
        "/assignments",
        json={"student_id": "STU101", "subject": "CS301", "title": "Assignment 4", "status": "Submitted on time", "score": "9.5"},
    )

    # 13. Bulk Import
    test_case(
        "Bulk Data Import",
        "POST",
        "/imports",
        json={
            "records": [
                {
                    "roll": "221101",
                    "name": "Aditya Kulkarni",
                    "division": "SEDA-A",
                    "attendance": 68.0,
                    "quiz": 58.0,
                    "assignment": 75.0,
                    "backlogs": 1,
                    "outcome": "Medium",
                }
            ],
            "semester": "sem5",
        },
    )

    print("==========================================================")
    print(f"SMOKE TEST SUMMARY: {passed}/{total} PASSED  ({failed} FAILED)")
    print("==========================================================")

    if failed > 0:
        sys.exit(1)
    else:
        print("[SUCCESS] All endpoints passed smoke test suite.")
        sys.exit(0)


if __name__ == "__main__":
    run_smoke_tests()
