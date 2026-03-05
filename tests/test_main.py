import pytest
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

Base.metadata.create_all(bind=engine)

def override_baza_olish():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def test_bosh_sahifa_no_query(db_session):
    # Add some test products
    product1 = models.Mahsulot(nomi="Olma", narxi=5000, miqdor=10)
    product2 = models.Mahsulot(nomi="Banan", narxi=8000, miqdor=15)
    db_session.add(product1)
    db_session.add(product2)
    db_session.commit()

    # Send a request to the root endpoint
    response = client.get("/")

    # Assert response status code is 200 OK
    assert response.status_code == 200

    # Assert response content is HTML
    assert "text/html" in response.headers["content-type"]

    # Assert both products are rendered in the HTML
    content = response.text
    assert "Olma" in content
    assert "Banan" in content
    assert "5,000" in content
    assert "8,000" in content


def test_bosh_sahifa_with_query(db_session):
    # Add some test products
    product1 = models.Mahsulot(nomi="Olma", narxi=5000, miqdor=10)
    product2 = models.Mahsulot(nomi="Olmali sharbat", narxi=12000, miqdor=5)
    product3 = models.Mahsulot(nomi="Banan", narxi=8000, miqdor=15)
    db_session.add(product1)
    db_session.add(product2)
    db_session.add(product3)
    db_session.commit()

    # Send a request with search query 'olma'
    response = client.get("/?q=olma")

    # Assert response status code is 200 OK
    assert response.status_code == 200

    # Assert response content is HTML
    content = response.text

    # Assert products matching the query are in the HTML
    assert "Olma" in content
    assert "Olmali sharbat" in content

    # Assert product not matching the query is NOT in the HTML
    assert "Banan" not in content

def test_bosh_sahifa_no_products():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

app.dependency_overrides[baza_olish] = override_baza_olish

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
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
