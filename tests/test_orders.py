import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.main import app, baza_olish
import os

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_sales.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from app import models

# Set up the database
models.Base.metadata.create_all(bind=engine)

def override_baza_olish():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[baza_olish] = override_baza_olish

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    yield

def test_orders_sahifa_empty():
    response = client.get("/orders")
    assert response.status_code == 200
    assert "Sotuvlar Tarixi" in response.text
    assert "Barcha Sotuvlar" in response.text

def test_orders_sahifa_with_data():
    db = TestingSessionLocal()
    try:
        mahsulot = models.Mahsulot(nomi="Olma", narxi=5000, miqdor=100)
        db.add(mahsulot)
        db.commit()
        db.refresh(mahsulot)

        sotuv = models.Sotuv(mahsulot_id=mahsulot.id, soni=5)
        db.add(sotuv)
        db.commit()
    finally:
        db.close()

    response = client.get("/orders")
    assert response.status_code == 200
    assert "Olma" in response.text
    assert "5 dona" in response.text
    assert "5,000 so‘m" in response.text
    assert "25,000 so‘m" in response.text
