import pytest
import os
import shutil
import io
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app, baza_olish
from app.database import Base
from app import models

# Set up in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency override
def override_baza_olish():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[baza_olish] = override_baza_olish
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Bosh sahifa testlari ---

def test_bosh_sahifa_no_query(db_session):
    product1 = models.Mahsulot(nomi="Olma", narxi=5000, miqdor=10)
    product2 = models.Mahsulot(nomi="Banan", narxi=8000, miqdor=15)
    db_session.add(product1)
    db_session.add(product2)
    db_session.commit()

    response = client.get("/")
    assert response.status_code == 200
    assert "Olma" in response.text
    assert "Banan" in response.text

def test_bosh_sahifa_with_query(db_session):
    product1 = models.Mahsulot(nomi="Olma", narxi=5000, miqdor=10)
    product2 = models.Mahsulot(nomi="Banan", narxi=8000, miqdor=15)
    db_session.add(product1)
    db_session.add(product2)
    db_session.commit()

    response = client.get("/?q=olma")
    assert response.status_code == 200
    assert "Olma" in response.text
    assert "Banan" not in response.text

# --- Mahsulot qo'shish testlari ---

def test_mahsulot_qoshish_without_image():
    response = client.post(
        "/mahsulot_qoshish",
        data={"nomi": "Test Mahsulot", "narxi": "10.5", "miqdor": "20"},
        follow_redirects=False
    )
    assert response.status_code == 303
    db = TestingSessionLocal()
    mahsulot = db.query(models.Mahsulot).filter(models.Mahsulot.nomi == "Test Mahsulot").first()
    assert mahsulot is not None
    db.close()

def test_mahsulot_qoshish_with_image(monkeypatch):
    file_content = b"fake image content"
    response = client.post(
        "/mahsulot_qoshish",
        data={"nomi": "Rasm Mahsulot", "narxi": "15.0", "miqdor": "5"},
        files={"rasm": ("test.png", io.BytesIO(file_content), "image/png")},
        follow_redirects=False
    )
    assert response.status_code == 303