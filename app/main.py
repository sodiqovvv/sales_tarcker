from fastapi import FastAPI, Depends, Request, Form, File, UploadFile, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app import models, auth, schemas
import shutil
import uuid
import os
from datetime import timedelta

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

async def get_current_user(request: Request, db: Session = Depends(baza_olish)):
    token = request.cookies.get("access_token")
    if not token:
        return None

    payload = auth.decode_access_token(token)
    if payload is None:
        return None

    username: str = payload.get("sub")
    if username is None:
        return None

    user = db.query(models.User).filter(models.User.username == username).first()
    return user

def login_required(user: models.User = Depends(get_current_user)):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"}
        )
    return user

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(baza_olish)
):
    try:
        schemas.UserCreate(username=username, password=password)
    except Exception as e:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Ma'lumotlar noto'g'ri: " + str(e)
        })

    db_user = db.query(models.User).filter(models.User.username == username).first()
    if db_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Foydalanuvchi nomi band"
        })

    hashed_password = auth.get_password_hash(password)
    new_user = models.User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    return RedirectResponse("/login", status_code=303)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(baza_olish)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not auth.verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Noto'g'ri foydalanuvchi nomi yoki parol"
        })

    access_token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    response = RedirectResponse("/", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("access_token")
    return response

@app.get("/", response_class=HTMLResponse)
def bosh_sahifa(
    request: Request,
    q: str = None,
    db: Session = Depends(baza_olish),
    user: models.User = Depends(login_required)
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


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.post("/mahsulot_qoshish")
def mahsulot_qoshish(
    nomi: str = Form(...),
    narxi: float = Form(...),
    miqdor: int = Form(...),
    rasm: UploadFile = File(None),
    db: Session = Depends(baza_olish),
    user: models.User = Depends(login_required)
):
    try:
        schemas.MahsulotYaratish(nomi=nomi, narxi=narxi, miqdor=miqdor)
    except Exception as e:
        # Simplistic error handling for now
        return RedirectResponse("/", status_code=303)

    rasm_url = None

    if rasm and rasm.filename:
        if not allowed_file(rasm.filename):
             return RedirectResponse("/", status_code=303)

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
    db: Session = Depends(baza_olish),
    user: models.User = Depends(login_required)
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
def ochirish(
    mahsulot_id: int,
    db: Session = Depends(baza_olish),
    user: models.User = Depends(login_required)
):
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
def orders_sahifa(
    request: Request,
    db: Session = Depends(baza_olish),
    user: models.User = Depends(login_required)
):
    sotuvlar = db.query(models.Sotuv).all()

    return templates.TemplateResponse("orders.html", {
        "request": request,
        "sotuvlar": sotuvlar
    })
