"""
Enumerações para tipos de tecido, caimento e tipo de peça.
"""
from enum import Enum

class FabricType(str, Enum):
    PLANO = "plano"       # tecido plano (algodão, linho, viscose, etc.)
    MALHA = "malha"       # malha (jersey, ribana, moletom, etc.)

class FitLevel(str, Enum):
    JUSTO   = "justo"     # colado ao corpo
    PADRAO  = "padrao"    # caimento normal
    AMPLO   = "amplo"     # folgado / oversized

class GarmentType(str, Enum):
    BLUSA       = "blusa"
    VESTIDO     = "vestido"
    CALCA       = "calca"
    SAIA        = "saia"
    CASACO      = "casaco"
    BODY        = "body"
