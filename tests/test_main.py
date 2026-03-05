import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, baza_olish
from app.database import Base

from sqlalchemy.pool import StaticPool

# Setup an in-memory SQLite database for testing

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_sotish_mahsulot_topilmadi():
    """
    Test missing product ID in `/sotish` edge case.
    """
    response = client.post(
        "/sotish",
        data={
            "mahsulot_id": 9999,
            "soni": 1
        },
        follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"
