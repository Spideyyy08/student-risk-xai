"""
Data Ingestion and Bulk CSV/JSON Import Service.
Validates records, reconciles student identities, creates raw academic records,
updates historical outcomes, triggers synchronous scoring, and records audit logs.
"""

from datetime import date, datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.student import Student
from app.models.subject import Subject
from app.models.attendance import AttendanceRecord
from app.models.assessment import Assessment
from app.models.assignment import Assignment
from app.models.semester_result import SemesterResult
from app.models.import_batch import ImportBatch
from app.models.audit_log import AuditLog
from app.services.prediction_service import score_and_store_prediction


def process_import_batch(
    db: Session,
    records: List[Any],
    semester_code: str = "sem5",
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    client_ip: Optional[str] = "127.0.0.1",
) -> Dict[str, Any]:
    """
    Ingest batch student performance records.
    Never fails the whole batch for one bad row.
    """
    rows_total = len(records)
    rows_ok = 0
    rows_failed = 0
    row_errors = []
    affected_students = set()

    # Subjects for semester
    subjects = db.scalars(select(Subject).where(Subject.semester_code == semester_code)).all()
    if not subjects:
        subjects = db.scalars(select(Subject)).all()

    today = date.today()

    for idx, raw in enumerate(records):
        row_num = idx + 1
        data = raw if isinstance(raw, dict) else raw.model_dump()

        try:
            roll = str(data.get("roll", "")).strip()
            if not roll:
                raise ValueError("Roll number is required.")

            att_val = float(data.get("attendance", 0))
            if att_val < 0.0 or att_val > 100.0:
                raise ValueError(f"Attendance {att_val}% out of range [0, 100].")

            quiz_val = float(data.get("quiz", 0))
            if quiz_val < 0.0 or quiz_val > 100.0:
                raise ValueError(f"Quiz score {quiz_val}% out of range [0, 100].")

            assign_val = float(data.get("assignment", 0))
            if assign_val < 0.0 or assign_val > 100.0:
                raise ValueError(f"Assignment completion {assign_val}% out of range [0, 100].")

            backlog_val = int(data.get("backlogs", 0))
            if backlog_val < 0 or backlog_val > 6:
                raise ValueError(f"Backlogs count {backlog_val} out of range [0, 6].")

            div = data.get("division")
            if div and div not in ["SEDA-A", "SEDA-B"]:
                raise ValueError(f"Division '{div}' must be 'SEDA-A' or 'SEDA-B'.")

            outcome = data.get("outcome")
            if outcome and outcome not in ["Low", "Medium", "High"]:
                raise ValueError(f"Outcome label '{outcome}' must be Low, Medium, or High.")

            # Student match or create
            student = db.scalar(select(Student).where(Student.roll == roll))
            if not student:
                name = data.get("name")
                if not name or not div:
                    raise ValueError(f"Student roll {roll} is not registered. Name and division are required to auto-enroll.")

                # Generate next STU code
                max_id = db.scalar(select(func.max(Student.id))) or 100
                student_code = f"STU{100 + max_id + 1}"
                student = Student(
                    student_code=student_code,
                    roll=roll,
                    name=name,
                    division=div,
                    is_active=True,
                )
                db.add(student)
                db.flush()

            affected_students.add(student.id)

            # Ingest raw records across subjects
            for subj in subjects:
                # 1. Attendance Snapshot
                att_rec = AttendanceRecord(
                    student_id=student.id,
                    subject_id=subj.id,
                    record_date=today,
                    attendance_pct=att_val,
                    classes_held=20,
                    classes_attended=int(round(att_val * 0.20)),
                )
                db.add(att_rec)

                # 2. Assessment
                assess_rec = Assessment(
                    student_id=student.id,
                    subject_id=subj.id,
                    name="Class Quiz",
                    kind="QUIZ",
                    score=quiz_val,
                    max_score=100.0,
                    assessed_on=today,
                )
                db.add(assess_rec)

                # 3. Assignment
                assign_rec = Assignment(
                    student_id=student.id,
                    subject_id=subj.id,
                    title="Assignment Import",
                    status="Submitted on time" if assign_val >= 75.0 else ("Submitted late" if assign_val >= 50.0 else "Defaulter (Missing)"),
                    score=round(assign_val / 10.0, 1),
                    submitted_on=today,
                )
                db.add(assign_rec)

            # 4. Previous semester result backlogs and optional outcome_label
            prev_sem_code = "sem4" if semester_code == "sem5" else "sem3"
            prev_result = db.scalar(
                select(SemesterResult).where(
                    SemesterResult.student_id == student.id,
                    SemesterResult.semester_code == prev_sem_code,
                )
            )
            if prev_result:
                prev_result.backlogs_count = backlog_val
                if outcome:
                    prev_result.outcome_label = outcome
            else:
                db.add(SemesterResult(
                    student_id=student.id,
                    semester_code=prev_sem_code,
                    sgpa=6.8,
                    backlogs_count=backlog_val,
                    outcome_label=outcome,
                ))

            rows_ok += 1
        except Exception as err:
            rows_failed += 1
            row_errors.append({"row": row_num, "message": str(err)})

    db.commit()

    # Recompute predictions for all affected students
    for st_id in affected_students:
        try:
            score_and_store_prediction(db, st_id, semester_code=semester_code)
        except Exception:
            pass

    # Record ImportBatch log
    import_batch = ImportBatch(
        user_id=user_id,
        filename=f"bulk_import_{today.isoformat()}.json",
        rows_total=rows_total,
        rows_ok=rows_ok,
        rows_failed=rows_failed,
        errors=row_errors,
    )
    db.add(import_batch)

    # Record AuditLog
    audit = AuditLog(
        user_id=user_id,
        username=username or "system",
        action="IMPORT",
        entity="IMPORT_BATCH",
        entity_id=str(import_batch.id or ""),
        ip=client_ip,
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "message": f"Successfully processed {rows_ok} of {rows_total} student records.",
        "rows_total": rows_total,
        "rows_ok": rows_ok,
        "rows_failed": rows_failed,
        "errors": row_errors,
    }
