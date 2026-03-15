from pydantic import BaseModel, Field, validator
from typing import Optional


class MahsulotYaratish(BaseModel):
    nomi: str = Field(..., min_length=2, max_length=100)
    narxi: float = Field(..., gt=0)
    miqdor: int = Field(..., ge=0)


class MahsulotJavob(MahsulotYaratish):
    id: int
    rasm: Optional[str] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str
