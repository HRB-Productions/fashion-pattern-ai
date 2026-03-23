"""
Testes unitários para ease_calculator.
Cobrir todos os casos da tabela de folgas.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import direto para evitar cadeia de imports pesados
from src.pattern.ease_calculator import calculate_ease, ease_per_quarter, EASE_TABLE
from src.models.enums import FabricType, FitLevel


def test_plano_justo_sem_manga():
    assert calculate_ease(FabricType.PLANO, FitLevel.JUSTO, False) == 2.0


def test_plano_justo_com_manga():
    assert calculate_ease(FabricType.PLANO, FitLevel.JUSTO, True) == 4.0


def test_plano_padrao_sem_manga():
    assert calculate_ease(FabricType.PLANO, FitLevel.PADRAO, False) == 3.0


def test_plano_padrao_com_manga():
    assert calculate_ease(FabricType.PLANO, FitLevel.PADRAO, True) == 5.0


def test_plano_amplo_sem_manga():
    assert calculate_ease(FabricType.PLANO, FitLevel.AMPLO, False) == 4.0


def test_plano_amplo_com_manga():
    assert calculate_ease(FabricType.PLANO, FitLevel.AMPLO, True) == 6.0


def test_malha_justo_negativo():
    assert calculate_ease(FabricType.MALHA, FitLevel.JUSTO, False) == -2.0


def test_malha_justo_com_manga():
    # Malha justo tem mesma folga com ou sem manga
    assert calculate_ease(FabricType.MALHA, FitLevel.JUSTO, True) == -2.0


def test_malha_padrao_zero():
    assert calculate_ease(FabricType.MALHA, FitLevel.PADRAO, False) == 0.0


def test_malha_padrao_com_manga():
    assert calculate_ease(FabricType.MALHA, FitLevel.PADRAO, True) == 0.0


def test_malha_amplo():
    assert calculate_ease(FabricType.MALHA, FitLevel.AMPLO, False) == 2.0
    assert calculate_ease(FabricType.MALHA, FitLevel.AMPLO, True) == 2.0


def test_ease_per_quarter():
    assert ease_per_quarter(2.0) == 0.5
    assert ease_per_quarter(-2.0) == -0.5
    assert ease_per_quarter(6.0) == 1.5
    assert ease_per_quarter(3.0) == 0.75
    assert ease_per_quarter(4.0) == 1.0
    assert ease_per_quarter(5.0) == 1.25
