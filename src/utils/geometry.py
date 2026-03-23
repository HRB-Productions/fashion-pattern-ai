"""
Helpers de geometria 2D para operações com moldes.
"""
from typing import List, Tuple
from src.models.pattern_piece import Point2D


def polygon_area(points: List[Point2D]) -> float:
    """
    Calcula área de um polígono usando fórmula de Shoelace.

    Args:
        points: Lista de (x, y) em ordem horária ou anti-horária

    Returns:
        Área em unidades quadradas
    """
    n = len(points)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    return abs(area) / 2.0


def polygon_centroid(points: List[Point2D]) -> Point2D:
    """
    Calcula centroide de um polígono.

    Args:
        points: Lista de (x, y) do contorno

    Returns:
        (cx, cy) do centroide
    """
    n = len(points)
    area = polygon_area(points)
    if area == 0:
        # Fallback: média simples
        cx = sum(p[0] for p in points) / n
        cy = sum(p[1] for p in points) / n
        return (cx, cy)

    cx = 0.0
    cy = 0.0
    for i in range(n):
        j = (i + 1) % n
        factor = points[i][0] * points[j][1] - points[j][0] * points[i][1]
        cx += (points[i][0] + points[j][0]) * factor
        cy += (points[i][1] + points[j][1]) * factor

    cx /= (6.0 * area)
    cy /= (6.0 * area)
    return (abs(cx), abs(cy))


def offset_polygon(points: List[Point2D], offset: float) -> List[Point2D]:
    """
    Expande ou contrai um polígono por um offset constante.

    Nota: Implementação simplificada. Para produção, usar shapely.

    Args:
        points: Contorno original
        offset: Distância para expandir (positivo) ou contrair (negativo)

    Returns:
        Lista de pontos offsetados
    """
    # Implementação simplificada: expandir cada ponto radialmente
    centroid = polygon_centroid(points)
    new_points = []

    for x, y in points:
        # Vetor do centroide ao ponto
        dx = x - centroid[0]
        dy = y - centroid[1]

        # Normalizar e aplicar offset
        import math
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0:
            scale = (dist + offset) / dist
            new_points.append((centroid[0] + dx * scale, centroid[1] + dy * scale))
        else:
            new_points.append((x, y))

    return new_points


def distance(p1: Point2D, p2: Point2D) -> float:
    """Distância euclidiana entre dois pontos."""
    import math
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def midpoint(p1: Point2D, p2: Point2D) -> Point2D:
    """Ponto médio entre dois pontos."""
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
