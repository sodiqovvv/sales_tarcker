from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Mahsulot(Base):
    __tablename__ = "mahsulotlar"

    id = Column(Integer, primary_key=True, index=True)
    nomi = Column(String, nullable=False)
    narxi = Column(Float, nullable=False)
    miqdor = Column(Integer, default=0)
    rasm = Column(String, nullable=True)

    sotuvlar = relationship(
        "Sotuv",
        back_populates="mahsulot",
        cascade="all, delete"
    )

class Sotuv(Base):
    __tablename__ = "sotuvlar"
    # Change this line in your Sotuv class

    id = Column(Integer, primary_key=True, index=True)
    mahsulot_id = Column(Integer, ForeignKey("mahsulotlar.id", ondelete="SET NULL"), nullable=True)
    soni = Column(Integer, nullable=False)
    vaqt = Column(DateTime, default=datetime.utcnow)

    mahsulot = relationship("Mahsulot", back_populates="sotuvlar")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)