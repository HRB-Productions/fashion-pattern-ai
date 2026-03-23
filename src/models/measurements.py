"""
Dataclass para medidas corporais com validação Pydantic.
Todos os campos em centímetros (float). Altura em cm também.
"""
from pydantic import BaseModel, field_validator

class BodyMeasurements(BaseModel):
    busto: float          # circunferência total do busto (cm)
    cintura: float        # circunferência da cintura fina (cm)
    quadril: float        # circunferência do quadril (cm)
    altura: float         # altura total (cm)
    comprimento_tronco: float | None = None   # opcional
    altura_busto: float | None = None       # do ombro ao ápice do busto

    @field_validator("busto")
    @classmethod
    def busto_valido(cls, v: float) -> float:
        if not 60 <= v <= 160:
            raise ValueError("Busto deve estar entre 60 e 160 cm")
        return v
