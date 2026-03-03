from fastapi import FastAPI, Depends, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app import models
import shutil
import uuid
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Savdo Hisoblash Ilovasi")

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def baza_olish():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def bosh_sahifa(
    request: Request,
    q: str = None,
    db: Session = Depends(baza_olish)
):
    query = db.query(models.Mahsulot)

    if q:
        query = query.filter(models.Mahsulot.nomi.ilike(f"%{q}%"))

    mahsulotlar = query.all()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "mahsulotlar": mahsulotlar,
        "q": q
    })


@app.post("/mahsulot_qoshish")
def mahsulot_qoshish(
    nomi: str = Form(...),
    narxi: float = Form(...),
    miqdor: int = Form(...),
    rasm: UploadFile = File(None),
    db: Session = Depends(baza_olish)
):
    rasm_url = None

    if rasm:
        os.makedirs("app/static/uploads", exist_ok=True)

        kengaytma = rasm.filename.split(".")[-1]
        yangi_nomi = f"{uuid.uuid4()}.{kengaytma}"
        saqlash_joyi = f"app/static/uploads/{yangi_nomi}"

        with open(saqlash_joyi, "wb") as buffer:
            shutil.copyfileobj(rasm.file, buffer)

        rasm_url = f"/static/uploads/{yangi_nomi}"

    yangi = models.Mahsulot(
        nomi=nomi,
        narxi=narxi,
        miqdor=miqdor,
        rasm=rasm_url
    )

    db.add(yangi)
    db.commit()

    return RedirectResponse("/", status_code=303)

@app.post("/sotish")
def sotish(
    mahsulot_id: int = Form(...),
    soni: int = Form(...),
    db: Session = Depends(baza_olish)
):
    mahsulot = db.query(models.Mahsulot).filter(
        models.Mahsulot.id == mahsulot_id
    ).first()

    if not mahsulot:
        return RedirectResponse("/", status_code=303)

    if mahsulot.miqdor < soni:
        return RedirectResponse("/", status_code=303)

    # Miqdorni kamaytirish
    mahsulot.miqdor -= soni

    # Sotuvni yozish
    yangi_sotuv = models.Sotuv(
        mahsulot_id=mahsulot.id,
        soni=soni
    )

    db.add(yangi_sotuv)
    db.commit()

    return RedirectResponse("/", status_code=303)

@app.post("/ochirish/{mahsulot_id}")
def ochirish(mahsulot_id: int, db: Session = Depends(baza_olish)):
    mahsulot = db.query(models.Mahsulot).filter(
        models.Mahsulot.id == mahsulot_id
    ).first()

    if not mahsulot:
        return RedirectResponse("/", status_code=303)

    # Agar rasm bo‘lsa, fayldan o‘chiramiz
    if mahsulot.rasm:
        rasm_path = "app" + mahsulot.rasm  # /static/uploads/... ni app/static/uploads/... ga aylantiramiz
        if os.path.exists(rasm_path):
            os.remove(rasm_path)

    db.delete(mahsulot)
    db.commit()

    return RedirectResponse("/", status_code=303)

@app.get("/orders", response_class=HTMLResponse)
def orders_sahifa(request: Request, db: Session = Depends(baza_olish)):
    sotuvlar = db.query(models.Sotuv).all()

    return templates.TemplateResponse("orders.html", {
        "request": request,
        "sotuvlar": sotuvlar
    })
