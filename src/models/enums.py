"""
Enumerações para tipos de tecido, caimento, tipo de peça e sistema de tamanhos.
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
    CAMISA      = "camisa"
    SHORT       = "short"
    CAMISETA    = "camiseta"
    MALHA_TOP   = "top"
    BERMUDA     = "bermuda"

class SizeSystem(str, Enum):
    BR = "BR"  # Brasil: PP, P, M, G, GG
    US = "US"  # EUA: XS, S, M, L, XL
    EU = "EU"  # Europa: 34, 38, 42, 46, 50
