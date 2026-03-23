"""
Tabelas de medidas padronizadas por sistema de tamanhos.

Baseado em médias industriais de modelagem.
"""
from typing import TypedDict
from enum import Enum


class SizeSystem(str, Enum):
    BR = "BR"  # Brasil: PP, P, M, G, GG
    US = "US"  # EUA: XS, S, M, L, XL
    EU = "EU"  # Europa: 34, 38, 42, 46, 50


class SizeMeasurements(TypedDict):
    """Medidas para um tamanho específico."""
    busto: float
    cintura: float
    quadril: float
    altura: float


# Sistema Brasileiro (BR)
SIZE_TABLE_BR: dict[str, SizeMeasurements] = {
    "PP": {"busto": 76.0, "cintura": 58.0, "quadril": 84.0, "altura": 160.0},
    "P":  {"busto": 82.0, "cintura": 64.0, "quadril": 90.0, "altura": 163.0},
    "M":  {"busto": 88.0, "cintura": 70.0, "quadril": 96.0, "altura": 165.0},
    "G":  {"busto": 96.0, "cintura": 78.0, "quadril": 104.0, "altura": 167.0},
    "GG": {"busto": 104.0, "cintura": 86.0, "quadril": 112.0, "altura": 170.0},
}

# Sistema Americano (US)
SIZE_TABLE_US: dict[str, SizeMeasurements] = {
    "XS": {"busto": 78.0, "cintura": 60.0, "quadril": 86.0, "altura": 160.0},
    "S":  {"busto": 84.0, "cintura": 66.0, "quadril": 92.0, "altura": 163.0},
    "M":  {"busto": 90.0, "cintura": 72.0, "quadril": 98.0, "altura": 165.0},
    "L":  {"busto": 98.0, "cintura": 80.0, "quadril": 106.0, "altura": 168.0},
    "XL": {"busto": 106.0, "cintura": 88.0, "quadril": 114.0, "altura": 170.0},
}

# Sistema Europeu (EU)
SIZE_TABLE_EU: dict[str, SizeMeasurements] = {
    "34": {"busto": 78.0, "cintura": 60.0, "quadril": 86.0, "altura": 162.0},
    "38": {"busto": 84.0, "cintura": 66.0, "quadril": 92.0, "altura": 165.0},
    "42": {"busto": 90.0, "cintura": 72.0, "quadril": 98.0, "altura": 167.0},
    "46": {"busto": 98.0, "cintura": 80.0, "quadril": 106.0, "altura": 168.0},
    "50": {"busto": 106.0, "cintura": 88.0, "quadril": 114.0, "altura": 170.0},
}

# Mapeamento de sistemas para tabelas
SIZE_TABLES: dict[str, dict[str, SizeMeasurements]] = {
    "BR": SIZE_TABLE_BR,
    "US": SIZE_TABLE_US,
    "EU": SIZE_TABLE_EU,
}


def get_size_measurements(system: str, size_label: str) -> SizeMeasurements | None:
    """
    Retorna medidas para um sistema e tamanho específicos.

    Args:
        system: Sistema de tamanhos ("BR", "US", "EU")
        size_label: Tamanho (ex: "M", "S", "42")

    Returns:
        Medidas ou None se não encontrado
    """
    table = SIZE_TABLES.get(system)
    if not table:
        return None

    return table.get(size_label)


def get_valid_sizes(system: str) -> list[str]:
    """Retorna lista de tamanhos válidos para um sistema."""
    table = SIZE_TABLES.get(system)
    if not table:
        return []
    return list(table.keys())


def is_valid_size(system: str, size_label: str) -> bool:
    """Verifica se um tamanho é válido para um sistema."""
    return get_size_measurements(system, size_label) is not None
