# Python 3.11 ni asos qilib olamiz
FROM python:3.11-slim

# Ishchi papkani belgilaymiz
WORKDIR /app

# Avval kutubxonalarni o'rnatamiz (Docker uchun tezroq bo'lishi uchun)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Barcha kodni konteynerga ko'chiramiz
COPY . .

# Gunicorn orqali ishga tushirish (Cloud Run uchun eng yaxshi variant)
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080"]