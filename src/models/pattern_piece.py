"""
Dataclass para peça de molde industrial.
"""
from dataclasses import dataclass, field
from typing import List, Tuple

Point2D = Tuple[float, float]

@dataclass
class PatternPiece:
    name: str                              # ex: "Frente", "Costas", "Manga"
    size: str                              # ex: "38", "M", "42"
    reference: str                         # ex: "BL-001-F"
    cut_quantity: int                      # quantas vezes cortar (1 ou 2)
    outline: List[Point2D]                 # contorno da peça em cm
    grain_line: Tuple[Point2D, Point2D]    # seta de fio do tecido
    seam_allowance_cm: float = 1.0         # margem padrão (hem usa 2.0)
    notches: List[Point2D] = field(default_factory=list)
    dart_apex: Point2D | None = None       # ápice da pence (se houver)
    instructions: str = ""                 # ex: "Cortar 2x no dobro"
