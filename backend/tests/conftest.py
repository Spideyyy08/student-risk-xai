"""
Pytest Test Fixtures and In-Memory Sandbox.
Trains a lightweight test model in-memory and overrides get_db with SQLite.
"""

import sys
from pathlib import Path
import pytest
from datetime import date
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
import shap

# Bootstrap sys.path
TEST_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TEST_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.student import Student
from app.models.semester import Semester
from app.models.subject import Subject
from app.models.attendance import AttendanceRecord
from app.models.assessment import Assessment
from app.models.assignment import Assignment
from app.models.semester_result import SemesterResult
from app.models.prediction import Prediction
from app.models.intervention import Intervention
from app.services.model_registry import model_bundle
from ml_pipeline.config import FEATURES, CLASS_TO_IDX

# SQLite In-Memory Database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_model():
    """Train a tiny in-memory model (400 rows) with classes [0, 1, 2] so tests are 100% self-contained."""
    rng = np.random.RandomState(42)
    n = 400
    X_mat = rng.uniform(20.0, 95.0, size=(n, len(FEATURES)))
    X_df = pd.DataFrame(X_mat, columns=FEATURES)

    # Deterministic balanced 3-class target: 0=Low, 1=Medium, 2=High
    y_int = rng.choice([0, 1, 2], size=n, p=[0.4, 0.3, 0.3])

    test_pipe = Pipeline([
        ("preprocessor", SimpleImputer(strategy="median")),
        ("classifier", DecisionTreeClassifier(max_depth=4, random_state=42)),
    ])
    test_pipe.fit(X_df, y_int)

    # Set up global model_bundle for test session
    model_bundle.pipeline = test_pipe
    model_bundle.classifier = test_pipe.named_steps["classifier"]
    model_bundle.explainer = shap.TreeExplainer(model_bundle.classifier)
    model_bundle.version = "test-v1"
    model_bundle.algorithm = "DecisionTree"
    model_bundle.is_loaded = True
    ev = model_bundle.explainer.expected_value
    model_bundle.base_value = float(ev[2]) if isinstance(ev, (list, np.ndarray)) else float(ev)
    model_bundle.metadata = {"version": "test-v1", "classes": ["Low", "Medium", "High"]}


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session with tables for each test function."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()

    # Seed core test data
    sem4 = Semester(code="sem4", label="Semester 4 (AY 2025-26)", academic_year="2025-26", is_current=False)
    sem5 = Semester(code="sem5", label="Semester 5 (AY 2026-27)", academic_year="2026-27", is_current=True)
    session.add_all([sem4, sem5])
    session.flush()

    s_dsa = Subject(code="CS301", name="Data Structures & Algorithms", short_name="DSA", semester_code="sem5")
    s_dbms = Subject(code="CS302", name="Database Management Systems", short_name="DBMS", semester_code="sem5")
    session.add_all([s_dsa, s_dbms])
    session.flush()

    # Test students
    st1 = Student(student_code="STU101", roll="221101", name="Aditya Kulkarni", division="SEDA-A", is_active=True)
    st2 = Student(student_code="STU102", roll="221102", name="Neha Joshi", division="SEDA-A", is_active=True)
    session.add_all([st1, st2])
    session.flush()

    # Academic records for STU101
    sr3 = SemesterResult(student_id=st1.id, semester_code="sem3", sgpa=6.12, backlogs_count=0)
    sr4 = SemesterResult(student_id=st1.id, semester_code="sem4", sgpa=5.84, backlogs_count=2, outcome_label="High")
    session.add_all([sr3, sr4])

    att1 = AttendanceRecord(student_id=st1.id, subject_id=s_dsa.id, record_date=date(2026, 10, 20), attendance_pct=54.0)
    att2 = AttendanceRecord(student_id=st1.id, subject_id=s_dbms.id, record_date=date(2026, 10, 20), attendance_pct=54.0)
    q1 = Assessment(student_id=st1.id, subject_id=s_dsa.id, name="Quiz 1", kind="QUIZ", score=46.0, max_score=100.0, assessed_on=date(2026, 10, 10))
    mid1 = Assessment(student_id=st1.id, subject_id=s_dsa.id, name="Mid-Sem", kind="MIDSEM", score=14.0, max_score=30.0, assessed_on=date(2026, 9, 15))
    lab1 = Assessment(student_id=st1.id, subject_id=s_dsa.id, name="Lab Test", kind="LABTEST", score=16.0, max_score=30.0, assessed_on=date(2026, 10, 15))
    as1 = Assignment(student_id=st1.id, subject_id=s_dsa.id, title="As1", status="Submitted late", score=5.0, submitted_on=date(2026, 10, 1))
    session.add_all([att1, att2, q1, mid1, lab1, as1])

    # Users
    u_admin = User(username="admin", password_hash=hash_password("admin123"), full_name="Admin", role="ADMIN", is_active=True)
    u_teacher = User(username="teacher", password_hash=hash_password("vit2026"), full_name="Teacher", role="TEACHER", is_active=True)
    u_student = User(username="student", password_hash=hash_password("student123"), full_name="Aditya", role="STUDENT", student_id=st1.id, is_active=True)
    session.add_all([u_admin, u_teacher, u_student])

    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db_session):
    """TestClient wired to in-memory database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def client_admin(client):
    token = create_access_token(subject="admin", role="ADMIN")
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
def client_teacher(client):
    token = create_access_token(subject="teacher", role="TEACHER")
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
def client_student(client):
    token = create_access_token(subject="student", role="STUDENT", student_id="STU101")
    client.headers["Authorization"] = f"Bearer {token}"
    return client
