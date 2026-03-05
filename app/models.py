from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Mahsulot:
    id: str
    nomi: str
    narxi: float
    miqdor: int = 0
    rasm: Optional[str] = None

@dataclass
class Sotuv:
    id: str
    mahsulot_id: Optional[str]
    soni: int
    vaqt: datetime
    mahsulot: Optional[Mahsulot] = None