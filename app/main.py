from fastapi import FastAPI, Depends, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from google.cloud import firestore
from app.database import get_db
from app import models
import shutil
import uuid
import os

app = FastAPI(title="Savdo Hisoblash Ilovasi")

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def baza_olish():
    return get_db()


@app.get("/", response_class=HTMLResponse)
def bosh_sahifa(
    request: Request,
    q: str = None,
    db: firestore.Client = Depends(baza_olish)
):
    # Fetch all documents from the "mahsulotlar" collection
    docs = db.collection('mahsulotlar').stream()

    mahsulotlar = []
    for doc in docs:
        doc_dict = doc.to_dict()
        if q and q.lower() not in doc_dict.get('nomi', '').lower():
            continue

        mahsulot = models.Mahsulot(
            id=doc.id,
            nomi=doc_dict.get('nomi', ''),
            narxi=doc_dict.get('narxi', 0.0),
            miqdor=doc_dict.get('miqdor', 0),
            rasm=doc_dict.get('rasm')
        )
        mahsulotlar.append(mahsulot)

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
    db: firestore.Client = Depends(baza_olish)
):
    rasm_url = None

    if rasm and rasm.filename:
        os.makedirs("app/static/uploads", exist_ok=True)

        kengaytma = rasm.filename.split(".")[-1]
        yangi_nomi = f"{uuid.uuid4()}.{kengaytma}"
        saqlash_joyi = f"app/static/uploads/{yangi_nomi}"

        with open(saqlash_joyi, "wb") as buffer:
            shutil.copyfileobj(rasm.file, buffer)

        rasm_url = f"/static/uploads/{yangi_nomi}"

    db.collection("mahsulotlar").add({
        "nomi": nomi,
        "narxi": narxi,
        "miqdor": miqdor,
        "rasm": rasm_url
    })

    return RedirectResponse("/", status_code=303)

@app.post("/sotish")
def sotish(
    mahsulot_id: str = Form(...),
    soni: int = Form(...),
    db: firestore.Client = Depends(baza_olish)
):
    mahsulot_ref = db.collection("mahsulotlar").document(mahsulot_id)
    mahsulot_doc = mahsulot_ref.get()

    if not mahsulot_doc.exists:
        return RedirectResponse("/", status_code=303)

    mahsulot_data = mahsulot_doc.to_dict()

    if mahsulot_data.get("miqdor", 0) < soni:
        return RedirectResponse("/", status_code=303)

    # Miqdorni kamaytirish
    mahsulot_ref.update({
        "miqdor": firestore.Increment(-soni)
    })

    # Sotuvni yozish
    db.collection("sotuvlar").add({
        "mahsulot_id": mahsulot_id,
        "soni": soni,
        "vaqt": firestore.SERVER_TIMESTAMP
    })

    return RedirectResponse("/", status_code=303)

@app.post("/ochirish/{mahsulot_id}")
def ochirish(mahsulot_id: str, db: firestore.Client = Depends(baza_olish)):
    mahsulot_ref = db.collection("mahsulotlar").document(mahsulot_id)
    mahsulot_doc = mahsulot_ref.get()

    if not mahsulot_doc.exists:
        return RedirectResponse("/", status_code=303)

    mahsulot_data = mahsulot_doc.to_dict()

    # Agar rasm bo‘lsa, fayldan o‘chiramiz
    rasm = mahsulot_data.get("rasm")
    if rasm:
        rasm_path = "app" + rasm  # /static/uploads/... ni app/static/uploads/... ga aylantiramiz
        if os.path.exists(rasm_path):
            os.remove(rasm_path)

    mahsulot_ref.delete()

    return RedirectResponse("/", status_code=303)

@app.get("/orders", response_class=HTMLResponse)
def orders_sahifa(request: Request, db: firestore.Client = Depends(baza_olish)):
    # Fetch all sales
    sotuvlar_docs = db.collection("sotuvlar").order_by("vaqt", direction=firestore.Query.DESCENDING).stream()

    sotuvlar = []
    # Optimization: Cache fetched mahsulot objects to avoid repeated reads for the same product
    mahsulot_cache = {}

    for doc in sotuvlar_docs:
        s_data = doc.to_dict()
        mahsulot_id = s_data.get("mahsulot_id")
        mahsulot = None

        if mahsulot_id:
            if mahsulot_id in mahsulot_cache:
                mahsulot = mahsulot_cache[mahsulot_id]
            else:
                m_doc = db.collection("mahsulotlar").document(mahsulot_id).get()
                if m_doc.exists:
                    m_data = m_doc.to_dict()
                    mahsulot = models.Mahsulot(
                        id=m_doc.id,
                        nomi=m_data.get("nomi", ""),
                        narxi=m_data.get("narxi", 0.0),
                        miqdor=m_data.get("miqdor", 0),
                        rasm=m_data.get("rasm")
                    )
                mahsulot_cache[mahsulot_id] = mahsulot

        # Handle Firestore datetime format safely
        vaqt = s_data.get("vaqt")

        sotuv = models.Sotuv(
            id=doc.id,
            mahsulot_id=mahsulot_id,
            soni=s_data.get("soni", 0),
            vaqt=vaqt,
            mahsulot=mahsulot
        )
        sotuvlar.append(sotuv)

    return templates.TemplateResponse("orders.html", {
        "request": request,
        "sotuvlar": sotuvlar
    })
