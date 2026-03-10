from fastapi import FastAPI, Depends, Request, Form, File, UploadFile, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from google.cloud import firestore
from app.database import get_db
from app import models, schemas, auth
import shutil
import uuid
import os

app = FastAPI(title="Savdo Hisoblash Ilovasi")

async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"}
        )
    payload = auth.decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"}
        )
    return payload.get("sub")

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

def baza_olish():
    return get_db()

@app.get("/login", response_class=HTMLResponse)
def login_sahifa(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: firestore.Client = Depends(baza_olish)
):
    users_ref = db.collection("users").where("username", "==", username).limit(1).get()
    if not users_ref:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Foydalanuvchi topilmadi"})

    user_doc = users_ref[0]
    user_data = user_doc.to_dict()

    if not auth.verify_password(password, user_data.get("password")):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Parol noto'g'ri"})

    access_token = auth.create_access_token(data={"sub": username})
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.get("/register", response_class=HTMLResponse)
def register_sahifa(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: firestore.Client = Depends(baza_olish)
):
    users_ref = db.collection("users").where("username", "==", username).limit(1).get()
    if users_ref:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Foydalanuvchi nomi band"})

    hashed_password = auth.get_password_hash(password)
    db.collection("users").add({
        "username": username,
        "password": hashed_password
    })
    return RedirectResponse("/login", status_code=303)

@app.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(key="access_token")
    return response

@app.get("/", response_class=HTMLResponse)
def bosh_sahifa(request: Request, q: str = None, db: firestore.Client = Depends(baza_olish), user: str = Depends(get_current_user)):
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

@app.post("/mahsulot_qoshish")
def mahsulot_qoshish(
    nomi: str = Form(...),
    narxi: float = Form(..., ge=0),
    miqdor: int = Form(..., ge=0),
    rasm: UploadFile = File(None),
    db: firestore.Client = Depends(baza_olish),
    user: str = Depends(get_current_user)
):
    rasm_url = None
    if rasm and rasm.filename:
        os.makedirs("app/static/uploads", exist_ok=True)
        yangi_nomi = f"{uuid.uuid4()}.{rasm.filename.split('.')[-1]}"
        saqlash_joyi = f"app/static/uploads/{yangi_nomi}"
        with open(saqlash_joyi, "wb") as buffer:
            shutil.copyfileobj(rasm.file, buffer)
        rasm_url = f"/static/uploads/{yangi_nomi}"

    db.collection("mahsulotlar").add({
        "nomi": nomi, "narxi": narxi, "miqdor": miqdor, "rasm": rasm_url
    })
    return RedirectResponse("/", status_code=303)

@app.post("/sotish")
def sotish(
    mahsulot_id: str = Form(...),
    soni: int = Form(..., ge=1),
    db: firestore.Client = Depends(baza_olish),
    user: str = Depends(get_current_user)
):
    mahsulot_ref = db.collection("mahsulotlar").document(mahsulot_id)
    doc = mahsulot_ref.get()
    if not doc.exists or doc.to_dict().get("miqdor", 0) < soni:
        return RedirectResponse("/", status_code=303)
    
    mahsulot_ref.update({"miqdor": firestore.Increment(-soni)})
    db.collection("sotuvlar").add({
        "mahsulot_id": mahsulot_id, "soni": soni, "vaqt": firestore.SERVER_TIMESTAMP
    })
    return RedirectResponse("/", status_code=303)

@app.get("/orders", response_class=HTMLResponse)
def sotuvlar_tarixi(
    request: Request,
    db: firestore.Client = Depends(baza_olish),
    user: str = Depends(get_current_user)
):
    docs = db.collection('sotuvlar').order_by('vaqt', direction=firestore.Query.DESCENDING).stream()
    sotuvlar = []
    for doc in docs:
        d = doc.to_dict()
        m_id = d.get('mahsulot_id')
        mahsulot = None
        if m_id:
            m_doc = db.collection('mahsulotlar').document(m_id).get()
            if m_doc.exists:
                md = m_doc.to_dict()
                mahsulot = models.Mahsulot(id=m_id, nomi=md.get('nomi',''), narxi=md.get('narxi',0.0))

        sotuvlar.append(models.Sotuv(
            id=doc.id,
            mahsulot_id=m_id,
            soni=d.get('soni', 0),
            vaqt=d.get('vaqt'),
            mahsulot=mahsulot
        ))
    return templates.TemplateResponse("orders.html", {"request": request, "sotuvlar": sotuvlar})

@app.post("/ochirish/{mahsulot_id}")
def ochirish(
    mahsulot_id: str,
    db: firestore.Client = Depends(baza_olish),
    user: str = Depends(get_current_user)
):
    ref = db.collection("mahsulotlar").document(mahsulot_id)
    doc = ref.get()
    if doc.exists:
        rasm = doc.to_dict().get("rasm")
        if rasm and os.path.exists("app" + rasm):
            os.remove("app" + rasm)
        ref.delete()
    return RedirectResponse("/", status_code=303)