"""
Gradação harmônica industrial para moldes.

REGRA DE GRADAÇÃO (por número de manequim, acumulativo):
  Ponto de decote    → mover +2 mm por número (horizontal)
  Ponto de ombro     → mover +3 mm por número (horizontal)
  Lateral da cava    → mover +5 mm por número (horizontal)
  Altura da cava     → mover +5 mm por número (vertical — abaixar a cava)
  Total por quarto   → 1 cm por número (2+3+5 = 10mm = 1cm ✓)

size_delta: inteiro positivo = subir manequim, negativo = descer
Ex: molde base tamanho 40, usuário quer 42 → size_delta = +2
"""
from src.models.pattern_piece import PatternPiece, Point2D
from copy import deepcopy

GRADE_RULES_MM = {
    "neckline":       2,    # mm por número
    "shoulder":       3,
    "armhole_side":   5,
    "armhole_height": 5,
}


def grade_piece(piece: PatternPiece, size_delta: int) -> PatternPiece:
    """
    Aplica gradação e retorna nova PatternPiece com contorno ajustado.

    Args:
        piece: PatternPiece original
        size_delta: número de manequins a subir (positivo) ou descer (negativo)

    Returns:
        Nova PatternPiece com pontos graduados
    """
    if size_delta == 0:
        return deepcopy(piece)

    new_piece = deepcopy(piece)

    # Converter mm para cm
    delta_mm = size_delta  # números de tamanho

    graded_outline = []
    for point in piece.outline:
        classification = classify_point(point, piece)
        rule_mm = GRADE_RULES_MM.get(classification, 0)

        # Aplicar offset horizontal
        offset_x = (rule_mm * delta_mm) / 10.0  # converter mm → cm

        # Aplicar offset vertical para pontos de altura da cava
        offset_y = 0.0
        if classification == "armhole_height":
            offset_y = (GRADE_RULES_MM["armhole_height"] * delta_mm) / 10.0

        new_x = point[0] + offset_x
        new_y = point[1] + offset_y
        graded_outline.append((new_x, new_y))

    new_piece.outline = graded_outline

    # Gradar também os notches
    new_notches = []
    for notch in piece.notches:
        classification = classify_point(notch, piece)
        rule_mm = GRADE_RULES_MM.get(classification, 0)
        offset_x = (rule_mm * delta_mm) / 10.0
        offset_y = 0.0
        if classification == "armhole_height":
            offset_y = (GRADE_RULES_MM["armhole_height"] * delta_mm) / 10.0
        new_notches.append((notch[0] + offset_x, notch[1] + offset_y))
    new_piece.notches = new_notches

    # Gradar grain_line
    start = piece.grain_line[0]
    end = piece.grain_line[1]
    # Grain line move proporcionalmente
    offset_x = (3 * delta_mm) / 10.0  # shoulder rule
    new_piece.grain_line = (
        (start[0] + offset_x, start[1]),
        (end[0] + offset_x, end[1])
    )

    # Gradar dart_apex se existir
    if piece.dart_apex:
        apex = piece.dart_apex
        offset_x = (2 * delta_mm) / 10.0  # neckline rule
        new_piece.dart_apex = (apex[0] + offset_x, apex[1])

    return new_piece


def classify_point(point: Point2D, piece: PatternPiece) -> str:
    """
    Classifica um ponto do outline para aplicar regra de gradação correta.

    Classifica como: neckline, shoulder, armhole_side, armhole_height,
                     waist, hip ou other.

    Args:
        point: (x, y) do ponto
        piece: PatternPiece de referência

    Returns:
        String com classificação do ponto
    """
    x, y = point

    # Encontrar limites da peça
    min_x = min(p[0] for p in piece.outline)
    max_x = max(p[0] for p in piece.outline)
    min_y = min(p[1] for p in piece.outline)
    max_y = max(p[1] for p in piece.outline)

    height = max_y - min_y
    width = max_x - min_x

    # Tolerâncias
    y_tol = height * 0.2  # 20% da altura
    x_tol = width * 0.15  # 15% da largura

    # Normalizar y relativo ao topo (min_y)
    y_rel = y - min_y

    # Decote: topo da peça (y_rel pequeno), perto do centro (x pequeno ou x=min_x)
    if y_rel < y_tol and x < min_x + width * 0.3:
        return "neckline"

    # Ombro: topo da peça, região intermediária (x entre 20% e 50% da largura)
    if y_rel < y_tol and x >= min_x + width * 0.2 and x < min_x + width * 0.5:
        return "shoulder"

    # Lateral da cava: lado direito (max_x), altura superior
    if x > max_x - x_tol and y_rel < height * 0.4:
        return "armhole_side"

    # Altura da cava: região da axila (y entre 20% e 50% da altura)
    if y_rel >= height * 0.2 and y_rel < height * 0.5 and x > min_x + width * 0.5:
        return "armhole_height"

    # Cintura: meio da peça verticalmente (40-60% da altura)
    if y_rel >= height * 0.4 and y_rel < height * 0.6:
        return "waist"

    # Quadril: parte inferior (>60% da altura)
    if y_rel >= height * 0.6:
        return "hip"

    return "other"
