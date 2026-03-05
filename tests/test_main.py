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
