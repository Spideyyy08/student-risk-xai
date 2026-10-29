"""
Database Seeding Script.
Populates standard 30-student cohort (15 SEDA-A, 15 SEDA-B), semester subjects,
raw attendance/assessment histories, demo users, interventions, and initial predictions.
Idempotent. --reset flag restricted strictly to development environment.
"""

import sys
import argparse
from datetime import date, datetime, timezone
from pathlib import Path

# Bootstrap sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.user import User
from app.models.student import Student
from app.models.semester import Semester
from app.models.subject import Subject
from app.models.attendance import AttendanceRecord
from app.models.assessment import Assessment
from app.models.assignment import Assignment
from app.models.semester_result import SemesterResult
from app.models.intervention import Intervention
from app.services.prediction_service import score_and_store_prediction
from app.services.model_registry import model_bundle

# 30 VIT Student Cohort (15 in SEDA-A, 15 in SEDA-B)
STUDENT_DATA = [
    # Division SEDA-A (15 students)
    {"id": "STU101", "roll": "221101", "name": "Aditya Kulkarni", "div": "SEDA-A", "att": 54, "quiz": 46, "assign": 50, "int": 14, "prac": 16, "bl": 2, "sgpa_s3": 6.12, "sgpa_s4": 5.84, "gender": "M"},
    {"id": "STU102", "roll": "221102", "name": "Neha Joshi", "div": "SEDA-A", "att": 62, "quiz": 52, "assign": 65, "int": 16, "prac": 18, "bl": 1, "sgpa_s3": 6.75, "sgpa_s4": 6.40, "gender": "F"},
    {"id": "STU103", "roll": "221103", "name": "Rohan Deshmukh", "div": "SEDA-A", "att": 48, "quiz": 38, "assign": 45, "int": 11, "prac": 14, "bl": 3, "sgpa_s3": 5.90, "sgpa_s4": 5.25, "gender": "M"},
    {"id": "STU104", "roll": "221104", "name": "Pooja Patil", "div": "SEDA-A", "att": 85, "quiz": 78, "assign": 90, "int": 24, "prac": 25, "bl": 0, "sgpa_s3": 8.10, "sgpa_s4": 8.35, "gender": "F"},
    {"id": "STU105", "roll": "221105", "name": "Siddharth Shinde", "div": "SEDA-A", "att": 76, "quiz": 68, "assign": 80, "int": 20, "prac": 21, "bl": 0, "sgpa_s3": 7.45, "sgpa_s4": 7.50, "gender": "M"},
    {"id": "STU106", "roll": "221106", "name": "Tanvi Gaikwad", "div": "SEDA-A", "att": 92, "quiz": 88, "assign": 95, "int": 27, "prac": 28, "bl": 0, "sgpa_s3": 8.90, "sgpa_s4": 9.15, "gender": "F"},
    {"id": "STU107", "roll": "221107", "name": "Aniket More", "div": "SEDA-A", "att": 58, "quiz": 50, "assign": 60, "int": 15, "prac": 17, "bl": 1, "sgpa_s3": 6.30, "sgpa_s4": 6.10, "gender": "M"},
    {"id": "STU108", "roll": "221108", "name": "Shruti Pawar", "div": "SEDA-A", "att": 82, "quiz": 74, "assign": 85, "int": 22, "prac": 23, "bl": 0, "sgpa_s3": 7.80, "sgpa_s4": 7.95, "gender": "F"},
    {"id": "STU109", "roll": "221109", "name": "Pranav Kadam", "div": "SEDA-A", "att": 70, "quiz": 64, "assign": 75, "int": 19, "prac": 20, "bl": 0, "sgpa_s3": 7.15, "sgpa_s4": 7.20, "gender": "M"},
    {"id": "STU110", "roll": "221110", "name": "Aishwarya Mane", "div": "SEDA-A", "att": 90, "quiz": 85, "assign": 92, "int": 26, "prac": 27, "bl": 0, "sgpa_s3": 8.65, "sgpa_s4": 8.80, "gender": "F"},
    {"id": "STU111", "roll": "221111", "name": "Omkar Bhosale", "div": "SEDA-A", "att": 66, "quiz": 58, "assign": 70, "int": 17, "prac": 19, "bl": 1, "sgpa_s3": 6.80, "sgpa_s4": 6.65, "gender": "M"},
    {"id": "STU112", "roll": "221112", "name": "Sayali Jadhav", "div": "SEDA-A", "att": 78, "quiz": 72, "assign": 82, "int": 21, "prac": 22, "bl": 0, "sgpa_s3": 7.60, "sgpa_s4": 7.75, "gender": "F"},
    {"id": "STU113", "roll": "221113", "name": "Gaurav Chavan", "div": "SEDA-A", "att": 52, "quiz": 44, "assign": 55, "int": 13, "prac": 15, "bl": 2, "sgpa_s3": 6.05, "sgpa_s4": 5.70, "gender": "M"},
    {"id": "STU114", "roll": "221114", "name": "Rutuja Salunkhe", "div": "SEDA-A", "att": 88, "quiz": 82, "assign": 88, "int": 25, "prac": 26, "bl": 0, "sgpa_s3": 8.40, "sgpa_s4": 8.55, "gender": "F"},
    {"id": "STU115", "roll": "221115", "name": "Harshada Mohite", "div": "SEDA-A", "att": 74, "quiz": 66, "assign": 78, "int": 19, "prac": 20, "bl": 0, "sgpa_s3": 7.30, "sgpa_s4": 7.40, "gender": "F"},

    # Division SEDA-B (15 students)
    {"id": "STU116", "roll": "221116", "name": "Tejas Sawant", "div": "SEDA-B", "att": 55, "quiz": 48, "assign": 52, "int": 14, "prac": 16, "bl": 2, "sgpa_s3": 6.20, "sgpa_s4": 5.90, "gender": "M"},
    {"id": "STU117", "roll": "221117", "name": "Snehal Raut", "div": "SEDA-B", "att": 64, "quiz": 56, "assign": 68, "int": 17, "prac": 18, "bl": 1, "sgpa_s3": 6.90, "sgpa_s4": 6.60, "gender": "F"},
    {"id": "STU118", "roll": "221118", "name": "Mayur Thorat", "div": "SEDA-B", "att": 45, "quiz": 35, "assign": 40, "int": 10, "prac": 13, "bl": 3, "sgpa_s3": 5.70, "sgpa_s4": 5.10, "gender": "M"},
    {"id": "STU119", "roll": "221119", "name": "Pratiksha Jagtap", "div": "SEDA-B", "att": 86, "quiz": 80, "assign": 91, "int": 25, "prac": 26, "bl": 0, "sgpa_s3": 8.25, "sgpa_s4": 8.45, "gender": "F"},
    {"id": "STU120", "roll": "221120", "name": "Abhishek Nalawade", "div": "SEDA-B", "att": 59, "quiz": 51, "assign": 62, "int": 15, "prac": 17, "bl": 1, "sgpa_s3": 6.45, "sgpa_s4": 6.25, "gender": "M"},
    {"id": "STU121", "roll": "221121", "name": "Vaishnavi Tambe", "div": "SEDA-B", "att": 94, "quiz": 90, "assign": 96, "int": 28, "prac": 29, "bl": 0, "sgpa_s3": 9.10, "sgpa_s4": 9.30, "gender": "F"},
    {"id": "STU122", "roll": "221122", "name": "Sanket Kamble", "div": "SEDA-B", "att": 72, "quiz": 65, "assign": 76, "int": 20, "prac": 21, "bl": 0, "sgpa_s3": 7.35, "sgpa_s4": 7.45, "gender": "M"},
    {"id": "STU123", "roll": "221123", "name": "Pallavi Ghorpade", "div": "SEDA-B", "att": 80, "quiz": 73, "assign": 84, "int": 22, "prac": 23, "bl": 0, "sgpa_s3": 7.75, "sgpa_s4": 7.85, "gender": "F"},
    {"id": "STU124", "roll": "221124", "name": "Kunal Sonawane", "div": "SEDA-B", "att": 51, "quiz": 42, "assign": 48, "int": 12, "prac": 15, "bl": 2, "sgpa_s3": 5.95, "sgpa_s4": 5.60, "gender": "M"},
    {"id": "STU125", "roll": "221125", "name": "Deepika Lokhande", "div": "SEDA-B", "att": 89, "quiz": 84, "assign": 90, "int": 26, "prac": 27, "bl": 0, "sgpa_s3": 8.50, "sgpa_s4": 8.70, "gender": "F"},
    {"id": "STU126", "roll": "221126", "name": "Ajinkya Bagal", "div": "SEDA-B", "att": 68, "quiz": 60, "assign": 72, "int": 18, "prac": 19, "bl": 1, "sgpa_s3": 7.00, "sgpa_s4": 6.80, "gender": "M"},
    {"id": "STU127", "roll": "221127", "name": "Manasi Shete", "div": "SEDA-B", "att": 77, "quiz": 70, "assign": 80, "int": 21, "prac": 22, "bl": 0, "sgpa_s3": 7.55, "sgpa_s4": 7.65, "gender": "F"},
    {"id": "STU128", "roll": "221128", "name": "Dhananjay Wagh", "div": "SEDA-B", "att": 61, "quiz": 53, "assign": 64, "int": 16, "prac": 18, "bl": 1, "sgpa_s3": 6.60, "sgpa_s4": 6.40, "gender": "M"},
    {"id": "STU129", "roll": "221129", "name": "Bhakti Nikam", "div": "SEDA-B", "att": 91, "quiz": 86, "assign": 94, "int": 27, "prac": 28, "bl": 0, "sgpa_s3": 8.80, "sgpa_s4": 9.00, "gender": "F"},
    {"id": "STU130", "roll": "221130", "name": "Akash Suryavanshi", "div": "SEDA-B", "att": 75, "quiz": 67, "assign": 79, "int": 20, "prac": 21, "bl": 0, "sgpa_s3": 7.40, "sgpa_s4": 7.50, "gender": "M"},
]


def seed(reset: bool = False):
    if reset:
        if settings.ENVIRONMENT.lower() != "development":
            print("[ERROR] Database reset is permitted only in 'development' environment.")
            sys.exit(1)
        print("Resetting database schema tables...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if already seeded
        existing_students = db.query(Student).count()
        if existing_students >= 30 and not reset:
            print("[INFO] Database already contains student cohort. Skipping re-seed.")
            return

        print("Seeding academic semesters...")
        sem4 = Semester(code="sem4", label="Semester 4 (AY 2025-26)", academic_year="2025-26", is_current=False)
        sem5 = Semester(code="sem5", label="Semester 5 (AY 2026-27)", academic_year="2026-27", is_current=True)
        db.add_all([sem4, sem5])
        db.flush()

        print("Seeding subjects for Sem 4 and Sem 5...")
        sem5_subjects = [
            Subject(code="CS301", name="Data Structures & Algorithms", short_name="DSA", semester_code="sem5"),
            Subject(code="CS302", name="Database Management Systems", short_name="DBMS", semester_code="sem5"),
            Subject(code="CS303", name="Discrete Mathematics", short_name="DM", semester_code="sem5"),
            Subject(code="CS304", name="Computer Organization & Architecture", short_name="COA", semester_code="sem5"),
            Subject(code="CS305", name="Python Programming", short_name="Python", semester_code="sem5"),
        ]
        sem4_subjects = [
            Subject(code="CS201", name="OOP with Java", short_name="Java", semester_code="sem4"),
            Subject(code="CS202", name="Operating Systems", short_name="OS", semester_code="sem4"),
            Subject(code="CS203", name="Microprocessor Architecture", short_name="Microprocessor", semester_code="sem4"),
            Subject(code="CS204", name="Software Engineering & Agile", short_name="SE", semester_code="sem4"),
            Subject(code="CS205", name="Computer Networks Fundamentals", short_name="CN", semester_code="sem4"),
        ]
        db.add_all(sem5_subjects + sem4_subjects)
        db.flush()

        print("Seeding 30 students and longitudinal academic records...")
        sem5_months = [
            date(2026, 5, 25), date(2026, 6, 25), date(2026, 7, 25),
            date(2026, 8, 25), date(2026, 9, 25), date(2026, 10, 25)
        ]
        student_entities = []

        for st in STUDENT_DATA:
            s_obj = Student(
                student_code=st["id"],
                roll=st["roll"],
                name=st["name"],
                division=st["div"],
                gender=st["gender"],
                is_active=True,
            )
            db.add(s_obj)
            db.flush()
            student_entities.append(s_obj)

            # Past semester results
            sr_s2 = SemesterResult(student_id=s_obj.id, semester_code="sem2", sgpa=round(st["sgpa_s3"] + 0.1, 2), backlogs_count=0, outcome_label="Low")
            sr_s3 = SemesterResult(student_id=s_obj.id, semester_code="sem3", sgpa=st["sgpa_s3"], backlogs_count=0 if st["bl"] == 0 else 1, outcome_label="Medium" if st["bl"] > 0 else "Low")
            sr_s4 = SemesterResult(student_id=s_obj.id, semester_code="sem4", sgpa=st["sgpa_s4"], backlogs_count=st["bl"], outcome_label="High" if st["bl"] >= 2 else ("Medium" if st["bl"] == 1 else "Low"))
            db.add_all([sr_s2, sr_s3, sr_s4])

            # Sem 5 raw records across 5 subjects
            base_att = float(st["att"])
            base_quiz = float(st["quiz"])
            base_int = float(st["int"])
            base_prac = float(st["prac"])
            base_assign = float(st["assign"])

            for idx, subj in enumerate(sem5_subjects):
                # Apply slight realistic subject variation
                offset = (idx - 2) * 2.5
                subj_att = max(20.0, min(100.0, base_att + offset))
                subj_quiz = max(15.0, min(100.0, base_quiz + offset))
                subj_int = max(4.0, min(30.0, base_int + offset * 0.2))
                subj_prac = max(6.0, min(30.0, base_prac + offset * 0.2))

                # 6 Monthly Attendance Snapshots
                for m_idx, m_date in enumerate(sem5_months):
                    drift = (m_idx - 5) * 1.2 if st["bl"] > 0 else (m_idx - 5) * -0.5
                    m_att = max(15.0, min(100.0, subj_att + drift))
                    att_rec = AttendanceRecord(
                        student_id=s_obj.id,
                        subject_id=subj.id,
                        record_date=m_date,
                        attendance_pct=round(m_att, 1),
                        classes_held=20,
                        classes_attended=int(round(m_att * 0.20)),
                    )
                    db.add(att_rec)

                # Assessments
                q1 = Assessment(student_id=s_obj.id, subject_id=subj.id, name="Quiz 1", kind="QUIZ", score=round(max(5.0, subj_quiz - 4.0), 1), max_score=100.0, assessed_on=date(2026, 7, 10))
                q2 = Assessment(student_id=s_obj.id, subject_id=subj.id, name="Quiz 2", kind="QUIZ", score=round(subj_quiz, 1), max_score=100.0, assessed_on=date(2026, 9, 20))
                mid = Assessment(student_id=s_obj.id, subject_id=subj.id, name="Mid-Sem", kind="MIDSEM", score=round(subj_int, 1), max_score=30.0, assessed_on=date(2026, 8, 15))
                lab = Assessment(student_id=s_obj.id, subject_id=subj.id, name="Lab Test", kind="LABTEST", score=round(subj_prac, 1), max_score=30.0, assessed_on=date(2026, 10, 10))
                db.add_all([q1, q2, mid, lab])

                # 4 Assignments
                for a_i in range(1, 5):
                    stat = "Submitted on time" if base_assign >= 75.0 else ("Submitted late" if base_assign >= 50.0 else "Defaulter (Missing)")
                    score_val = max(1.0, min(10.0, round(base_assign / 10.0, 1)))
                    assign_rec = Assignment(
                        student_id=s_obj.id,
                        subject_id=subj.id,
                        title=f"Assignment {a_i}",
                        status=stat,
                        score=score_val,
                        submitted_on=date(2026, 6 + a_i, 15),
                    )
                    db.add(assign_rec)

        db.flush()

        print("Seeding demo users...")
        u_admin = User(
            username="admin",
            password_hash=hash_password("admin123"),
            full_name="Head of Department (Admin)",
            role="ADMIN",
            department="Computer Engineering",
            is_active=True,
        )
        u_teacher = User(
            username="teacher",
            password_hash=hash_password("vit2026"),
            full_name="Prof. A. S. Sharma",
            role="TEACHER",
            department="Computer Engineering",
            is_active=True,
        )
        u_student = User(
            username="student",
            password_hash=hash_password("student123"),
            full_name="Aditya Kulkarni (Student)",
            role="STUDENT",
            student_id=student_entities[0].id,
            department="Computer Engineering",
            is_active=True,
        )
        db.add_all([u_admin, u_teacher, u_student])
        db.flush()

        print("Seeding initial faculty interventions...")
        interventions = [
            Intervention(student_id=student_entities[0].id, semester_code="sem5", type="Counselling", status="Planned", intervention_date=date(2026, 10, 25), notes="Initial discussion regarding low attendance and backlog plan", created_by=u_teacher.id),
            Intervention(student_id=student_entities[1].id, semester_code="sem5", type="Extra class", status="In progress", intervention_date=date(2026, 10, 22), notes="Attending Saturday DSA problem-solving sessions", created_by=u_teacher.id),
            Intervention(student_id=student_entities[2].id, semester_code="sem5", type="Parent meeting", status="Completed", intervention_date=date(2026, 10, 18), notes="Discussed semester recovery plan with parents", created_by=u_teacher.id),
            Intervention(student_id=student_entities[15].id, semester_code="sem5", type="Mentor assigned", status="In progress", intervention_date=date(2026, 10, 20), notes="Paired with senior student mentor for DBMS normalization", created_by=u_teacher.id),
            Intervention(student_id=student_entities[16].id, semester_code="sem5", type="Counselling", status="Completed", intervention_date=date(2026, 10, 15), notes="Reviewed concept gaps in Discrete Mathematics", created_by=u_teacher.id),
            Intervention(student_id=student_entities[19].id, semester_code="sem5", type="Extra class", status="Planned", intervention_date=date(2026, 10, 26), notes="Enrolled in weekly remedial laboratory session", created_by=u_teacher.id),
        ]
        db.add_all(interventions)
        db.commit()

        print("Running initial predictions and personalized recommendations for cohort...")
        # Ensure model is ready
        if not model_bundle.is_loaded:
            model_bundle.load()

        predictions = []
        for s in student_entities:
            p = score_and_store_prediction(db, s.id, semester_code="sem5")
            predictions.append((s, p))

        # Risk distribution summary
        risk_counts = {"High": 0, "Medium": 0, "Low": 0}
        for _, p in predictions:
            risk_counts[p.risk_level] = risk_counts.get(p.risk_level, 0) + 1

        print("\n========================================================")
        print("COHORT SEEDING COMPLETE - ACADEMIC RISK SUMMARY")
        print("========================================================")
        print(f"Total Cohort:    {len(student_entities)} students (15 SEDA-A, 15 SEDA-B)")
        print(f"High Risk:       {risk_counts['High']:2d} ({risk_counts['High']/30*100:5.1f}%)")
        print(f"Medium Risk:     {risk_counts['Medium']:2d} ({risk_counts['Medium']/30*100:5.1f}%)")
        print(f"Low Risk:        {risk_counts['Low']:2d} ({risk_counts['Low']/30*100:5.1f}%)")

        # Top 5 Highest Risk Students ASCII Table
        sorted_by_risk = sorted(predictions, key=lambda x: -x[1].p_high)[:5]
        print("\nTop 5 Highest Risk Students (by P(High)):")
        print("ID     | Roll   | Name                 | Div    | Risk   | P(High) | Att% | Bl | Key Factor")
        print("-------+--------+----------------------+--------+--------+---------+------+----+---------------------------")
        for st_obj, p_obj in sorted_by_risk:
            kf = p_obj.shap[0]["label"] if p_obj.shap else "Attendance"
            print(f"{st_obj.student_code:<6} | {st_obj.roll:<6} | {st_obj.name:<20} | {st_obj.division:<6} | {p_obj.risk_level:<6} | {p_obj.p_high:<7.2f} | {int(round(p_obj.features.get('attendance_pct', 0))):<4} | {int(round(p_obj.features.get('backlogs', 0))):<2} | {kf}")
        print("========================================================\n")

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Seed academic risk database.")
    parser.add_argument("--reset", action="store_true", help="Reset all tables before seeding (development only).")
    args = parser.parse_args()
    seed(reset=args.reset)


if __name__ == "__main__":
    main()
