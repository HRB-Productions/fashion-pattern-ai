"""
Testes para gradação harmônica industrial.
Verificar que delta=0 não altera o molde e que delta=+1 aumenta conforme regras.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pattern.grading import grade_piece, GRADE_RULES_MM, classify_point
from src.models.pattern_piece import PatternPiece, Point2D


@pytest.fixture
def sample_piece():
    """Piece de exemplo para testes."""
    return PatternPiece(
        name="Frente",
        size="40",
        reference="BL-001-F",
        cut_quantity=2,
        outline=[
            (0.0, 0.0),      # decote centro
            (7.0, 0.0),      # decote lado
            (7.0, -9.0),     # decote curva
            (12.0, -7.5),    # ombro
            (25.0, 10.0),    # cava lateral
            (25.0, 20.0),    # cintura
            (25.0, 30.0),    # quadril
            (25.0, 40.0),    # barra
            (0.0, 40.0),     # centro frente
        ],
        grain_line=((12.5, 5.0), (12.5, 35.0)),
        seam_allowance_cm=1.0,
        notches=[(12.0, -7.5), (25.0, 10.0)],
        instructions="Cortar 2x no dobro",
    )


def test_delta_zero_nao_altera(sample_piece):
    """Delta zero deve retornar peça idêntica."""
    graded = grade_piece(sample_piece, size_delta=0)
    assert graded.outline == sample_piece.outline
    assert graded.grain_line == sample_piece.grain_line
    assert graded.notches == sample_piece.notches


def test_gradacao_positiva_aumenta_peca(sample_piece):
    """Delta +1 deve aumentar largura conforme regra armhole_side (5mm)."""
    graded = grade_piece(sample_piece, size_delta=1)

    orig_width = max(p[0] for p in sample_piece.outline)
    new_width = max(p[0] for p in graded.outline)

    # Largura deve aumentar 5mm (regra armhole_side)
    assert abs((new_width - orig_width) - 0.5) < 0.05  # tolerância 0.5mm


def test_gradacao_negativa_diminui_ponto_lateral(sample_piece):
    """Delta -1 deve diminuir pontos laterais conforme regra armhole_side (5mm)."""
    graded = grade_piece(sample_piece, size_delta=-1)

    # Verificar ponto específico da cava lateral
    orig_cava = sample_piece.outline[4]  # (25.0, 10.0)
    new_cava = graded.outline[4]

    # Cava lateral deve diminuir 5mm (regra armhole_side)
    assert abs((orig_cava[0] - new_cava[0]) - 0.5) < 0.05  # tolerância 0.5mm


def test_classify_point_decote(sample_piece):
    """Pontos no topo/centro devem ser classificados como neckline."""
    point = (0.0, 0.0)  # centro do decote
    classification = classify_point(point, sample_piece)
    assert classification == "neckline"


def test_classify_point_ombro(sample_piece):
    """Pontos na região do ombro devem ser classificados como shoulder."""
    point = (12.0, -7.5)  # região do ombro
    classification = classify_point(point, sample_piece)
    assert classification == "shoulder"


def test_classify_point_cava_lateral(sample_piece):
    """Pontos na lateral da cava devem ser armhole_side."""
    point = (25.0, 10.0)  # lateral da cava
    classification = classify_point(point, sample_piece)
    assert classification == "armhole_side"


def test_grain_line_gradada(sample_piece):
    """Grain line deve ser deslocada horizontalmente."""
    graded = grade_piece(sample_piece, size_delta=1)

    orig_start_x = sample_piece.grain_line[0][0]
    new_start_x = graded.grain_line[0][0]

    # Grain line segue regra shoulder (3mm por número)
    expected_offset = 3 / 10.0  # 3mm → cm
    assert abs((new_start_x - orig_start_x) - expected_offset) < 0.01


def test_notches_gradados(sample_piece):
    """Notches devem ser graduados conforme sua classificação."""
    graded = grade_piece(sample_piece, size_delta=1)

    # Verificar que notches foram modificados
    assert len(graded.notches) == len(sample_piece.notches)

    orig_notch = sample_piece.notches[0]
    new_notch = graded.notches[0]

    # Notch de ombro deve mover ~3mm
    assert new_notch[0] > orig_notch[0]  # aumentou horizontalmente
