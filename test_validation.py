import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_mahsulot_qoshish_negative_price():
    response = client.post(
        "/mahsulot_qoshish",
        data={
            "nomi": "Test Product",
            "narxi": -10.0,
            "miqdor": 5
        }
    )
    # Validation error because price < 0
    assert response.status_code == 422
    assert "greater_than_equal" in response.json()["detail"][0]["type"]

def test_mahsulot_qoshish_negative_quantity():
    response = client.post(
        "/mahsulot_qoshish",
        data={
            "nomi": "Test Product",
            "narxi": 10.0,
            "miqdor": -5
        }
    )
    # Validation error because quantity < 0
    assert response.status_code == 422
    assert "greater_than_equal" in response.json()["detail"][0]["type"]

def test_sotish_zero_quantity():
    response = client.post(
        "/sotish",
        data={
            "mahsulot_id": 1,
            "soni": 0
        }
    )
    # Validation error because quantity < 1
    assert response.status_code == 422
    assert "greater_than_equal" in response.json()["detail"][0]["type"]

def test_sotish_negative_quantity():
    response = client.post(
        "/sotish",
        data={
            "mahsulot_id": 1,
            "soni": -5
        }
    )
    # Validation error because quantity < 1
    assert response.status_code == 422
    assert "greater_than_equal" in response.json()["detail"][0]["type"]

if __name__ == "__main__":
    pytest.main(["-v", __file__])
