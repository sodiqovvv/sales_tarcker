from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from app.main import app, baza_olish
from app.database import Base
from app import models

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

app.dependency_overrides[baza_olish] = override_baza_olish

client = TestClient(app)

@pytest.fixture(autouse=True)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)



    assert response.status_code == 303
    assert response.headers["location"] == "/"

    db = TestingSessionLocal()
    db.close()



    assert response.status_code == 303

    db = TestingSessionLocal()
    db.close()
