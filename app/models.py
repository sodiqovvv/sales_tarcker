from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
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

    id = Column(Integer, primary_key=True, index=True)
    mahsulot_id = Column(Integer, ForeignKey("mahsulotlar.id", ondelete="SET NULL"), nullable=True)
    soni = Column(Integer, nullable=False)
    vaqt = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    mahsulot = relationship("Mahsulot", back_populates="sotuvlar")