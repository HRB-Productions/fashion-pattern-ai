"""
Testes para DiagramBuilder.
Verificar fórmulas obrigatórias e estrutura das peças.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pattern.diagram_builder import DiagramBuilder
from src.models.measurements import BodyMeasurements
from src.vision.garment_classifier import GarmentFeatures
from src.models.enums import FabricType, GarmentType


@pytest.fixture
def sample_measurements():
    """Medidas de exemplo."""
    return BodyMeasurements(
        busto=88.0,
        cintura=70.0,
        quadril=95.0,
        altura=165.0,
    )


@pytest.fixture
def sample_features_sem_manga():
    """Características sem mangas."""
    return GarmentFeatures(
        fabric_type=FabricType.PLANO,
        garment_type=GarmentType.BLUSA,
        has_sleeves=False,
        neckline="redondo",
        has_dart=False,
    )


@pytest.fixture
def sample_features_com_manga():
    """Características com mangas."""
    return GarmentFeatures(
        fabric_type=FabricType.PLANO,
        garment_type=GarmentType.BLUSA,
        has_sleeves=True,
        neckline="redondo",
        has_dart=False,
    )


def test_build_front_largura_correta(sample_measurements, sample_features_sem_manga):
    """Frente deve ter largura = busto/4 + 1.0."""
    builder = DiagramBuilder(sample_measurements, sample_features_sem_manga)
    front = builder.build_front()

    expected_width = sample_measurements.busto / 4 + 1.0
    actual_width = max(p[0] for p in front.outline)

    assert abs(actual_width - expected_width) < 0.1


def test_build_back_largura_correta(sample_measurements, sample_features_sem_manga):
    """Costas deve ter largura = busto/4 - 1.0."""
    builder = DiagramBuilder(sample_measurements, sample_features_sem_manga)
    back = builder.build_back()

    expected_width = sample_measurements.busto / 4 - 1.0
    actual_width = max(p[0] for p in back.outline)

    assert abs(actual_width - expected_width) < 0.1


def test_frente_mais_larga_que_costas(sample_measurements, sample_features_sem_manga):
    """Frente deve ser 2cm mais larga que costas."""
    builder = DiagramBuilder(sample_measurements, sample_features_sem_manga)

    front_width = max(p[0] for p in builder.build_front().outline)
    back_width = max(p[0] for p in builder.build_back().outline)

    assert abs(front_width - back_width - 2.0) < 0.1


def test_build_all_retorna_frente_e_costas(sample_measurements, sample_features_sem_manga):
    """build_all deve retornar frente e costas."""
    builder = DiagramBuilder(sample_measurements, sample_features_sem_manga)
    pieces = builder.build_all()

    assert len(pieces) == 2
    assert pieces[0].name == "Frente"
    assert pieces[1].name == "Costas"


def test_build_all_com_manga_inclui_manga(sample_measurements, sample_features_com_manga):
    """Com has_sleeves=True, deve incluir manga."""
    builder = DiagramBuilder(sample_measurements, sample_features_com_manga)
    pieces = builder.build_all()

    assert len(pieces) == 3
    assert pieces[2].name == "Manga"


def test_grain_line_presente(sample_measurements, sample_features_sem_manga):
    """Todas as peças devem ter grain_line."""
    builder = DiagramBuilder(sample_measurements, sample_features_sem_manga)
    pieces = builder.build_all()

    for piece in pieces:
        assert piece.grain_line is not None
        assert len(piece.grain_line) == 2


def test_notches_presentes(sample_measurements, sample_features_sem_manga):
    """Peças devem ter notches nas cavas."""
    builder = DiagramBuilder(sample_measurements, sample_features_sem_manga)
    front = builder.build_front()
    back = builder.build_back()

    assert len(front.notches) >= 2
    assert len(back.notches) >= 2


def test_altura_cava_formula(sample_measurements, sample_features_sem_manga):
    """Altura da cava deve seguir fórmula: busto/8 + 3.0."""
    builder = DiagramBuilder(sample_measurements, sample_features_sem_manga)
    front = builder.build_front()

    expected_cava_height = sample_measurements.busto / 8 + 3.0

    # Verificar que ponto da cava está na altura esperada
    cava_point = front.notches[1]  # fundo da cava
    assert abs(cava_point[1] - expected_cava_height) < 2.0  # tolerância maior
