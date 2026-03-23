"""
Testes para pdf_generator.
Verificar geração de PDF em escala 1:1.
"""
import pytest
import tempfile
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from src.export.pdf_generator import export_to_pdf, _tile_to_a4
from src.models.pattern_piece import PatternPiece


@pytest.fixture
def sample_piece():
    """Peça de exemplo."""
    return PatternPiece(
        name="Frente",
        size="40",
        reference="BL-001-F",
        cut_quantity=2,
        outline=[
            (0.0, 0.0),
            (25.0, 0.0),
            (25.0, 40.0),
            (0.0, 40.0),
        ],
        grain_line=((12.5, 5.0), (12.5, 35.0)),
        notches=[(25.0, 10.0)],
        instructions="Cortar 2x",
    )


@pytest.fixture
def large_piece():
    """Peça grande que requer múltiplas páginas A4."""
    return PatternPiece(
        name="Vestido",
        size="40",
        reference="VD-001-F",
        cut_quantity=2,
        outline=[
            (0.0, 0.0),
            (50.0, 0.0),
            (50.0, 120.0),
            (0.0, 120.0),
        ],
        grain_line=((25.0, 10.0), (25.0, 110.0)),
        notches=[(50.0, 20.0)],
        instructions="Cortar 2x",
    )


def test_export_to_pdf_cria_arquivo(sample_piece, tmp_path):
    """Deve criar arquivo PDF."""
    output_path = tmp_path / "test.pdf"
    result = export_to_pdf([sample_piece], str(output_path))

    assert Path(result).exists()
    assert Path(result).stat().st_size > 0


def test_export_to_pdf_retorna_path_correto(sample_piece, tmp_path):
    """Deve retornar caminho do arquivo gerado."""
    output_path = tmp_path / "test.pdf"
    result = export_to_pdf([sample_piece], str(output_path))

    assert result == str(output_path)


def test_tile_to_a4_pequena_cabem_uma_pagina():
    """Peça pequena (15x20cm) deve caber em uma página."""
    tiles = _tile_to_a4(15.0, 20.0)  # 15x20 cm
    assert len(tiles) == 1


def test_tile_to_a4_grande_requer_multiplas_paginas():
    """Peça grande requer múltiplas páginas."""
    tiles = _tile_to_a4(50.0, 120.0)  # 50x120 cm
    assert len(tiles) > 1


def test_export_multiple_pieces(sample_piece, large_piece, tmp_path):
    """Exportar múltiplas peças."""
    output_path = tmp_path / "multi.pdf"
    result = export_to_pdf([sample_piece, large_piece], str(output_path))

    assert Path(result).exists()
    assert Path(result).stat().st_size > 0


def test_pdf_com_dart_apex(tmp_path):
    """Peça com dart_apex deve renderizar círculo."""
    piece = PatternPiece(
        name="Frente",
        size="40",
        reference="BL-001-F",
        cut_quantity=2,
        outline=[
            (0.0, 0.0),
            (25.0, 0.0),
            (25.0, 40.0),
            (0.0, 40.0),
        ],
        grain_line=((12.5, 5.0), (12.5, 35.0)),
        dart_apex=(12.5, 20.0),
        instructions="Cortar 2x",
    )

    output_path = tmp_path / "dart.pdf"
    result = export_to_pdf([piece], str(output_path))

    assert Path(result).exists()
