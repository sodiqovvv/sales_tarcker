from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
import os
import shutil
import io

from app.main import app, baza_olish
from app.database import Base
from app import models

# In-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
from sqlalchemy.pool import StaticPool

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_uploads_dir():
    # Setup test uploads directory
    test_dir = "app/static/test_uploads"
    os.makedirs(test_dir, exist_ok=True)
    yield test_dir
    # Cleanup test uploads directory
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

def test_mahsulot_qoshish_without_image():
    response = client.post(
        "/mahsulot_qoshish",
        data={
            "nomi": "Test Mahsulot",
            "narxi": "10.5",
            "miqdor": "20"
        },
        follow_redirects=False # So we can check the 303 status
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"

    # Check if the product was actually added to DB
    db = TestingSessionLocal()
    mahsulot = db.query(models.Mahsulot).filter(models.Mahsulot.nomi == "Test Mahsulot").first()
    assert mahsulot is not None
    assert mahsulot.narxi == 10.5
    assert mahsulot.miqdor == 20
    assert mahsulot.rasm is None
    db.close()


def test_mahsulot_qoshish_with_image(test_uploads_dir, monkeypatch):
    # Create a fake image file
    file_content = b"fake image content"
    file_like = io.BytesIO(file_content)

    # Patch the saqlash_joyi path logic in main.py to save in test_uploads_dir
    # Since main.py hardcodes "app/static/uploads", let's mock os.makedirs to do nothing
    # and open to open in the test directory.
    # Actually, a better way is to patch the logic or verify the response.
    # Wait, the main.py code explicitly does:
    # saqlash_joyi = f"app/static/uploads/{yangi_nomi}"
    # Instead of mocking complex things, we can just intercept the created file and delete it.

    # Let's track files before
    uploads_dir = "app/static/uploads"
    os.makedirs(uploads_dir, exist_ok=True)
    files_before = set(os.listdir(uploads_dir))

    response = client.post(
        "/mahsulot_qoshish",
        data={
            "nomi": "Rasm Mahsulot",
            "narxi": "15.0",
            "miqdor": "5"
        },
        files={
            "rasm": ("test_image.png", file_like, "image/png")
        },
        follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"

    # Check if the product was added with the image url
    db = TestingSessionLocal()
    mahsulot = db.query(models.Mahsulot).filter(models.Mahsulot.nomi == "Rasm Mahsulot").first()
    assert mahsulot is not None
    assert mahsulot.rasm is not None
    assert mahsulot.rasm.startswith("/static/uploads/")
    assert mahsulot.rasm.endswith(".png")

    # Verify the file was actually saved
    # rasm format is like /static/uploads/uuid.png
    # file path should be app/static/uploads/uuid.png
    file_path = "app" + mahsulot.rasm
    assert os.path.exists(file_path)

    # Clean up the file created by the test
    files_after = set(os.listdir(uploads_dir))
    new_files = files_after - files_before
    for f in new_files:
        os.remove(os.path.join(uploads_dir, f))

    db.close()

def test_mahsulot_qoshish_validation_error():
    # Missing narxi
    response = client.post(
        "/mahsulot_qoshish",
        data={
            "nomi": "Invalid Mahsulot",
            "miqdor": "5"
        }
    )

    # FastAPI returns 422 for validation errors on missing Form fields
    assert response.status_code == 422
