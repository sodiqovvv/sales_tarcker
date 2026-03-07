from fastapi import FastAPI, Depends, Request, Form, File, UploadFile, HTTPException, status, Response
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

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

def baza_olish():
    return get_db()

async def get_current_user(request: Request, db: firestore.Client = Depends(baza_olish)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = auth.decode_access_token(token)
    if not payload:
        return None
    username = payload.get("sub")
    if not username:
        return None
    # Check if user exists in Firestore
    user_ref = db.collection("users").document(username).get()
    if not user_ref.exists:
        return None
    return username

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: firestore.Client = Depends(baza_olish)
):
    user_ref = db.collection("users").document(username).get()
    if not user_ref.exists:
        return templates.TemplateResponse("login.html", {"request": {}, "error": "Foydalanuvchi topilmadi"})

    user_data = user_ref.to_dict()
    if not auth.verify_password(password, user_data.get("hashed_password")):
        return templates.TemplateResponse("login.html", {"request": {}, "error": "Noto'g'ri parol"})

    token = auth.create_access_token(data={"sub": username})
    res = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    res.set_cookie(key="access_token", value=token, httponly=True)
    return res

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(
    username: str = Form(...),
    password: str = Form(...),
    db: firestore.Client = Depends(baza_olish)
):
    user_ref = db.collection("users").document(username).get()
    if user_ref.exists:
        return templates.TemplateResponse("register.html", {"request": {}, "error": "Bu foydalanuvchi nomi band"})

    hashed_password = auth.get_password_hash(password)
    db.collection("users").document(username).set({
        "username": username,
        "hashed_password": hashed_password
    })
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/logout")
async def logout():
    res = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    res.delete_cookie("access_token")
    return res

@app.get("/", response_class=HTMLResponse)
def bosh_sahifa(request: Request, q: str = None, db: firestore.Client = Depends(baza_olish), current_user: str = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
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
    current_user: str = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
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
    current_user: str = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
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
async def orders_page(
    request: Request,
    db: firestore.Client = Depends(baza_olish),
    current_user: str = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    docs = db.collection('sotuvlar').order_by('vaqt', direction=firestore.Query.DESCENDING).stream()
    sotuvlar = []
    for doc in docs:
        d = doc.to_dict()
        m_id = d.get('mahsulot_id')
        m_ref = db.collection('mahsulotlar').document(m_id).get() if m_id else None

        m_obj = None
        if m_ref and m_ref.exists:
            md = m_ref.to_dict()
            m_obj = models.Mahsulot(id=m_ref.id, nomi=md.get('nomi'), narxi=md.get('narxi', 0))

        sotuv = models.Sotuv(
            id=doc.id,
            mahsulot_id=m_id,
            soni=d.get('soni', 0),
            vaqt=d.get('vaqt'),
            mahsulot=m_obj
        )
        sotuvlar.append(sotuv)

    return templates.TemplateResponse("orders.html", {"request": request, "sotuvlar": sotuvlar})

@app.post("/ochirish/{mahsulot_id}")
def ochirish(
    mahsulot_id: str,
    db: firestore.Client = Depends(baza_olish),
    current_user: str = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    ref = db.collection("mahsulotlar").document(mahsulot_id)
    doc = ref.get()
    if doc.exists:
        rasm = doc.to_dict().get("rasm")
        if rasm and os.path.exists("app" + rasm):
            os.remove("app" + rasm)
        ref.delete()
    return RedirectResponse("/", status_code=303)