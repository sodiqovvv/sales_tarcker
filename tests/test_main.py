<<<<<<< HEAD
import pytest
from app import models

def test_bosh_sahifa(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Savdo Hisoblash Ilovasi" in response.text

def test_bosh_sahifa_with_query(client, db_session):
    # Add some dummy products
    p1 = models.Mahsulot(nomi="Olma", narxi=5000, miqdor=10)
    p2 = models.Mahsulot(nomi="Uzum", narxi=7000, miqdor=5)
    db_session.add_all([p1, p2])
    db_session.commit()

    response = client.get("/?q=ol")
    assert response.status_code == 200
    assert "Olma" in response.text
    assert "Uzum" not in response.text

def test_mahsulot_qoshish(client, db_session):
    response = client.post(
        "/mahsulot_qoshish",
        data={"nomi": "Shaftoli", "narxi": 8000.0, "miqdor": 20},
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"

    mahsulot = db_session.query(models.Mahsulot).filter_by(nomi="Shaftoli").first()
    assert mahsulot is not None
    assert mahsulot.narxi == 8000.0
    assert mahsulot.miqdor == 20

def test_sotish_success(client, db_session):
    p1 = models.Mahsulot(nomi="Olma", narxi=5000, miqdor=10)
    db_session.add(p1)
    db_session.commit()
    db_session.refresh(p1)

    response = client.post(
        "/sotish",
        data={"mahsulot_id": p1.id, "soni": 3},
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"

    # Check that quantity is reduced
    db_session.refresh(p1)
    assert p1.miqdor == 7

    # Check that sale was recorded
    sotuv = db_session.query(models.Sotuv).first()
    assert sotuv is not None
    assert sotuv.mahsulot_id == p1.id
    assert sotuv.soni == 3

def test_sotish_not_found(client, db_session):
    response = client.post(
        "/sotish",
        data={"mahsulot_id": 999, "soni": 3},
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"

    sotuvlar = db_session.query(models.Sotuv).all()
    assert len(sotuvlar) == 0

def test_sotish_insufficient_quantity(client, db_session):
    p1 = models.Mahsulot(nomi="Olma", narxi=5000, miqdor=2)
    db_session.add(p1)
    db_session.commit()
    db_session.refresh(p1)

    response = client.post(
        "/sotish",
        data={"mahsulot_id": p1.id, "soni": 5},
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"

    # Quantity shouldn't change
    db_session.refresh(p1)
    assert p1.miqdor == 2

    # Sale shouldn't be recorded
    sotuvlar = db_session.query(models.Sotuv).all()
    assert len(sotuvlar) == 0

def test_ochirish_success(client, db_session):
    p1 = models.Mahsulot(nomi="Olma", narxi=5000, miqdor=10)
    db_session.add(p1)
    db_session.commit()
    db_session.refresh(p1)

    response = client.post(
        f"/ochirish/{p1.id}",
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"

    mahsulot = db_session.query(models.Mahsulot).filter_by(id=p1.id).first()
    assert mahsulot is None

def test_ochirish_not_found(client, db_session):
    response = client.post(
        "/ochirish/999",
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"

def test_orders_sahifa(client, db_session):
    p1 = models.Mahsulot(nomi="Olma", narxi=5000, miqdor=10)
    db_session.add(p1)
    db_session.commit()
    db_session.refresh(p1)
    s1 = models.Sotuv(mahsulot_id=p1.id, soni=2)
    db_session.add(s1)
    db_session.commit()

    response = client.get("/orders")
    assert response.status_code == 200
    # The response template might output sotuvlar, though we only assert status 200 to be safe on string matching.
=======
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
>>>>>>> main
