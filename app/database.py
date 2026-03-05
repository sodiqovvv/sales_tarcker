from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# 1. Render'dagi Environment Variable'ni o'qiymiz
json_data = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")

if not json_data:
    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS_JSON topilmadi! Render muhitini tekshiring.")

# 2. JSON matnini lug'atga o'giramiz
key_dict = json.loads(json_data)

SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass
