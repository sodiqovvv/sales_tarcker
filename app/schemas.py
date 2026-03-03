from pydantic import BaseModel


class MahsulotYaratish(BaseModel):
    nomi: str
    narxi: float


class MahsulotJavob(MahsulotYaratish):
    id: int

    class Config:
        from_attributes = True