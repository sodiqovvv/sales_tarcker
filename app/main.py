from fastapi import FastAPI, Depends, Request, Form, File, UploadFile, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from google.cloud import firestore
from app.database import get_db
from app import models, schemas
import shutil
import uuid
import os

app = FastAPI(title="Savdo Hisoblash Ilovasi")

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

def baza_olish():
    return get_db()

@app.get("/", response_class=HTMLResponse)
def bosh_sahifa(request: Request, q: str = None, db: firestore.Client = Depends(baza_olish)):
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
    return templates.TemplateResponse("index.html", {"request": request, "mahsulotlar": mahsulotlar, "q": q})

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "svg"}

@app.post("/mahsulot_qoshish")
def mahsulot_qoshish(
    nomi: str = Form(..., min_length=2, max_length=100),
    narxi: float = Form(..., ge=0),
    miqdor: int = Form(..., ge=0),
    rasm: UploadFile = File(None),
    db: firestore.Client = Depends(baza_olish)
):
    rasm_url = None
    if rasm and rasm.filename:
        ext = rasm.filename.split('.')[-1].lower()
        if ext not in ALLOWED_EXTENSIONS or not rasm.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Faqat rasm fayllari ruxsat etiladi (jpg, jpeg, png, webp, svg).")

        os.makedirs("app/static/uploads", exist_ok=True)
        yangi_nomi = f"{uuid.uuid4()}.{ext}"
        saqlash_joyi = f"app/static/uploads/{yangi_nomi}"
        with open(saqlash_joyi, "wb") as buffer:
            shutil.copyfileobj(rasm.file, buffer)
        rasm_url = f"/static/uploads/{yangi_nomi}"

    db.collection("mahsulotlar").add({
        "nomi": nomi, "narxi": narxi, "miqdor": miqdor, "rasm": rasm_url
    })
    return RedirectResponse("/", status_code=303)

@app.post("/sotish")
def sotish(mahsulot_id: str = Form(...), soni: int = Form(..., ge=1), db: firestore.Client = Depends(baza_olish)):
    mahsulot_ref = db.collection("mahsulotlar").document(mahsulot_id)
    doc = mahsulot_ref.get()
    if not doc.exists or doc.to_dict().get("miqdor", 0) < soni:
        return RedirectResponse("/", status_code=303)
    
    mahsulot_ref.update({"miqdor": firestore.Increment(-soni)})
    db.collection("sotuvlar").add({
        "mahsulot_id": mahsulot_id, "soni": soni, "vaqt": firestore.SERVER_TIMESTAMP
    })
    return RedirectResponse("/", status_code=303)

@app.post("/ochirish/{mahsulot_id}")
def ochirish(mahsulot_id: str, db: firestore.Client = Depends(baza_olish)):
    ref = db.collection("mahsulotlar").document(mahsulot_id)
    doc = ref.get()
    if doc.exists:
        rasm_path = doc.to_dict().get("rasm")
        if rasm_path:
            # Prevent path traversal by ensuring we only delete from the uploads directory
            safe_filename = os.path.basename(rasm_path)
            full_path = os.path.join("app/static/uploads", safe_filename)
            if os.path.isfile(full_path):
                os.remove(full_path)
        ref.delete()
    return RedirectResponse("/", status_code=303)