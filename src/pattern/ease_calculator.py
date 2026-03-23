"""
Calculadora de folga industrial para moldes.

TABELA DE FOLGAS (cm totais no busto):
  Tecido plano:
    justo   sem manga  → +2.0    justo   com manga  → +4.0
    padrão  sem manga  → +3.0    padrão  com manga  → +5.0
    amplo   sem manga  → +4.0    amplo   com manga  → +6.0

  Malha:
    justo              → -2.0  (redução)
    padrão             → 0.0
    amplo              → +2.0

A folga é distribuída em 4 partes iguais (por quarto do busto).
"""
from src.models.enums import FabricType, FitLevel
from src.models.pattern_piece import PatternPiece

EASE_TABLE = {
    FabricType.PLANO: {
        FitLevel.JUSTO:   {False: 2.0,  True: 4.0},
        FitLevel.PADRAO:  {False: 3.0,  True: 5.0},
        FitLevel.AMPLO:   {False: 4.0,  True: 6.0},
    },
    FabricType.MALHA: {
        FitLevel.JUSTO:   {False: -2.0, True: -2.0},
        FitLevel.PADRAO:  {False: 0.0,  True:  0.0},
        FitLevel.AMPLO:   {False: 2.0,  True:  2.0},
    },
}


def calculate_ease(
    fabric_type: FabricType,
    fit_level: FitLevel,
    has_sleeves: bool
) -> float:
    """
    Retorna folga TOTAL em cm para o busto.

    Args:
        fabric_type: Tipo de tecido (plano ou malha)
        fit_level: Nível de caimento (justo, padrao, amplo)
        has_sleeves: Se a peça tem mangas

    Returns:
        Folga total em cm (pode ser negativa para malha justa)
    """
    return EASE_TABLE[fabric_type][fit_level][has_sleeves]


def ease_per_quarter(total_ease: float) -> float:
    """
    Folga por quarto do busto.

    Ex: folga total de 2cm → 0.5cm por quarto.
    """
    return total_ease / 4


def apply_ease_to_pieces(
    pieces: list[PatternPiece],
    fabric_type: FabricType,
    fit_level: FitLevel,
    has_sleeves: bool
) -> list[PatternPiece]:
    """
    Aplica a folga calculada ao contorno de todas as peças.
    Expande (ou contrai) o outline lateralmente.

    Args:
        pieces: Lista de PatternPiece originais
        fabric_type: Tipo de tecido
        fit_level: Nível de caimento
        has_sleeves: Se tem mangas

    Returns:
        Lista de PatternPiece com folga aplicada
    """
    from copy import deepcopy

    eq = ease_per_quarter(calculate_ease(fabric_type, fit_level, has_sleeves))

    modified_pieces = []

    for piece in pieces:
        # Criar cópia profunda
        new_piece = deepcopy(piece)

        # Aplicar expansão/contração nas laterais
        # Identificar pontos laterais (maior X) e aplicar offset
        new_outline = []
        for x, y in piece.outline:
            # Classificar ponto para saber quanto offset aplicar
            if _is_side_point(x, piece):
                # Lateral: aplicar folga completa
                new_x = x + eq
            elif _is_center_point(x, piece):
                # Centro: não aplicar folga (mantém origem)
                new_x = x
            else:
                # Pontos intermediários: interpolar
                max_x = max(p[0] for p in piece.outline)
                if max_x > 0:
                    ratio = x / max_x
                    new_x = x + eq * ratio
                else:
                    new_x = x
            new_outline.append((new_x, y))

        new_piece.outline = new_outline
        modified_pieces.append(new_piece)

    return modified_pieces


def _is_side_point(x: float, piece: PatternPiece) -> bool:
    """Verifica se ponto é lateral (max X da peça)."""
    max_x = max(p[0] for p in piece.outline)
    return abs(x - max_x) < 0.5  # tolerância 0.5cm


def _is_center_point(x: float, piece: PatternPiece) -> bool:
    """Verifica se ponto é central (x = 0 ou próximo)."""
    return abs(x) < 0.5  # tolerância 0.5cm
