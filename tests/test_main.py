import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from unittest.mock import patch

from app.main import app, baza_olish
from app.database import Base
from app import models

# Test database URL (SQLite in-memory)
from sqlalchemy.pool import StaticPool

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def override_baza_olish():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[baza_olish] = override_baza_olish

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    # Setup: clear the tables before each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown: clear the tables after each test
    Base.metadata.drop_all(bind=engine)

def add_test_mahsulot(db, nomi="Test Product", narxi=100.0, miqdor=10, rasm=None):
    mahsulot = models.Mahsulot(nomi=nomi, narxi=narxi, miqdor=miqdor, rasm=rasm)
    db.add(mahsulot)
    db.commit()
    db.refresh(mahsulot)
    return mahsulot

def test_ochirish_success_no_image():
    # Setup
    db = TestingSessionLocal()
    mahsulot = add_test_mahsulot(db, rasm=None)
    mahsulot_id = mahsulot.id
    db.close()

    # Act
    response = client.post(f"/ochirish/{mahsulot_id}")

    # Assert
    assert response.status_code == 200 # Redirects generally return 200 in TestClient when following redirects by default
    # To check if it was truly deleted, check the DB
    db = TestingSessionLocal()
    deleted_mahsulot = db.query(models.Mahsulot).filter(models.Mahsulot.id == mahsulot_id).first()
    db.close()
    assert deleted_mahsulot is None

@patch("os.path.exists")
@patch("os.remove")
def test_ochirish_success_with_image(mock_remove, mock_exists):
    # Setup
    db = TestingSessionLocal()
    test_image_path = "/static/uploads/test_image.jpg"
    mahsulot = add_test_mahsulot(db, rasm=test_image_path)
    mahsulot_id = mahsulot.id
    db.close()

    mock_exists.return_value = True

    # Act
    # When following redirects, status is 200
    response = client.post(f"/ochirish/{mahsulot_id}")

    # Assert
    assert response.status_code == 200

    # Ensure os.path.exists and os.remove were called with the correct path
    expected_full_path = "app" + test_image_path
    mock_exists.assert_called_once_with(expected_full_path)
    mock_remove.assert_called_once_with(expected_full_path)

    # Ensure it's deleted from DB
    db = TestingSessionLocal()
    deleted_mahsulot = db.query(models.Mahsulot).filter(models.Mahsulot.id == mahsulot_id).first()
    db.close()
    assert deleted_mahsulot is None

def test_ochirish_not_found():
    # Attempt to delete a non-existent product
    response = client.post("/ochirish/999", follow_redirects=False)

    # Should redirect to "/"
    assert response.status_code == 303
    assert response.headers["location"] == "/"

@patch("os.path.exists")
@patch("os.remove")
def test_ochirish_success_with_image_file_not_found(mock_remove, mock_exists):
    # Setup
    db = TestingSessionLocal()
    test_image_path = "/static/uploads/test_image_missing.jpg"
    mahsulot = add_test_mahsulot(db, rasm=test_image_path)
    mahsulot_id = mahsulot.id
    db.close()

    # The DB record has an image path, but it doesn't exist on disk
    mock_exists.return_value = False

    # Act
    response = client.post(f"/ochirish/{mahsulot_id}", follow_redirects=False)

    # Assert
    assert response.status_code == 303

    # Ensure os.path.exists was called
    expected_full_path = "app" + test_image_path
    mock_exists.assert_called_once_with(expected_full_path)

    # Ensure os.remove was NOT called
    mock_remove.assert_not_called()

    # Ensure it's still deleted from DB
    db = TestingSessionLocal()
    deleted_mahsulot = db.query(models.Mahsulot).filter(models.Mahsulot.id == mahsulot_id).first()
    db.close()
    assert deleted_mahsulot is None
