"""
Gerador de preview de molde em PNG.
Cria uma imagem de pré-visualização do molde completo para o usuário conferir.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import List
from src.models.pattern_piece import PatternPiece


# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 123, 254)
RED = (255, 59, 48)
GREEN = (52, 199, 89)


def draw_piece_outline(
    draw: ImageDraw.ImageDraw,
    piece: PatternPiece,
    offset_x: float,
    offset_y: float,
    scale: float = 10.0,
) -> None:
    """
    Desenha o contorno de uma peça no canvas.

    Args:
        draw: ImageDraw do PIL
        piece: PatternPiece com pontos
        offset_x: Posição X no canvas
        offset_y: Posição Y no canvas
        scale: Pixels por cm
    """
    if not piece.outline:
        return

    # Converter pontos para pixels
    pixel_points = []
    for pt in piece.outline:
        px = offset_x + float(pt[0]) * scale
        py = offset_y + float(pt[1]) * scale
        pixel_points.append((px, py))

    # Desenhar contorno
    if len(pixel_points) > 1:
        draw.line(pixel_points + [pixel_points[0]], fill=BLACK, width=2)


def draw_grain_line(
    draw: ImageDraw.ImageDraw,
    piece: PatternPiece,
    offset_x: float,
    offset_y: float,
    scale: float = 10.0,
) -> None:
    """Desenha a linha de fibra no molde."""
    if not piece.grain_line:
        return

    start, end = piece.grain_line
    x1 = offset_x + float(start[0]) * scale
    y1 = offset_y + float(start[1]) * scale
    x2 = offset_x + float(end[0]) * scale
    y2 = offset_y + float(end[1]) * scale

    draw.line([(x1, y1), (x2, y2)], fill=BLUE, width=2)

    # Desenhar setas nas extremidades
    arrow_size = 8
    draw.polygon([
        (x2 - arrow_size, y2 - arrow_size),
        (x2 + arrow_size, y2 - arrow_size),
        (x2, y2)
    ], fill=BLUE)


def draw_notches(
    draw: ImageDraw.ImageDraw,
    piece: PatternPiece,
    offset_x: float,
    offset_y: float,
    scale: float = 10.0,
) -> None:
    """Desenha as marcações (notches) no molde."""
    if not piece.notches:
        return

    for notch in piece.notches:
        nx = offset_x + float(notch[0]) * scale
        ny = offset_y + float(notch[1]) * scale
        draw.ellipse([nx-3, ny-3, nx+3, ny+3], fill=RED)


def draw_label(
    draw: ImageDraw.ImageDraw,
    piece: PatternPiece,
    offset_x: float,
    offset_y: float,
    font: ImageFont.FreeTypeFont = None,
) -> None:
    """Desenha o label/nome da peça e instruções."""
    label = f"{piece.name}\n{piece.reference}\n{piece.instructions}"
    if font is None:
        font = ImageFont.load_default()

    draw.text((offset_x + 5, offset_y + 5), label, fill=BLACK, font=font)


def draw_curves(
    draw: ImageDraw.ImageDraw,
    piece: PatternPiece,
    offset_x: float,
    offset_y: float,
    scale: float = 10.0,
) -> None:
    """Desenha curvas Bezier no molde."""
    if not piece.curves:
        return

    for curve in piece.curves:
        pts = curve.get('pontos_controle', [])
        if not pts or len(pts) < 2:
            continue
            
        # Converter para coordenadas do canvas
        pixel_pts = [
            (offset_x + float(p[0]) * scale, offset_y + float(p[1]) * scale)
            for p in pts
        ]
        
        # Desenhar curva (aproximada por segmentos lineares)
        if len(pixel_pts) == 2:
            draw.line(pixel_pts, fill=BLACK, width=2)
        elif len(pixel_pts) >= 3:
            points = []
            steps = 20
            for i in range(steps + 1):
                t = i / steps
                if len(pixel_pts) == 3: # Quadrática
                    p0, p1, p2 = pixel_pts
                    x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
                    y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
                elif len(pixel_pts) == 4: # Cúbica
                    p0, p1, p2, p3 = pixel_pts
                    x = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t)*t**2 * p2[0] + t**3 * p3[0]
                    y = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t)*t**2 * p2[1] + t**3 * p3[1]
                else:
                    points = pixel_pts
                    break
                points.append((x, y))
            
            if points:
                draw.line(points, fill=BLACK, width=2)


def draw_dimensions(
    draw: ImageDraw.ImageDraw,
    piece: PatternPiece,
    offset_x: float,
    offset_y: float,
    scale: float = 10.0,
    font: ImageFont.FreeTypeFont = None
) -> None:
    """Desenha cotas técnicas no molde."""
    if not piece.dimensions:
        return

    for dim in piece.dimensions:
        start = dim['start']
        end = dim['end']
        label = dim['label']
        
        x1 = offset_x + float(start[0]) * scale
        y1 = offset_y + float(start[1]) * scale
        x2 = offset_x + float(end[0]) * scale
        y2 = offset_y + float(end[1]) * scale
        
        # Linha da cota (cinza claro)
        draw.line([(x1, y1), (x2, y2)], fill=GRAY, width=1)
        
        # Pequenos traços perpendiculares nas pontas
        if dim['type'] == 'h':
            draw.line([(x1, y1-5), (x1, y1+5)], fill=GRAY, width=1)
            draw.line([(x2, y2-5), (x2, y2+5)], fill=GRAY, width=1)
        else:
            draw.line([(x1-5, y1), (x1+5, y1)], fill=GRAY, width=1)
            draw.line([(x2-5, y2), (x2+5, y2)], fill=GRAY, width=1)

        # Texto da cota
        if font is None:
            font = ImageFont.load_default()
        
        tx = (x1 + x2) / 2
        ty = (y1 + y2) / 2
        draw.text((tx - 10, ty - 10), label, fill=BLACK, font=font)


def generate_preview(
    pieces: List[PatternPiece],
    output_path: str,
    title: str = "Fashion Pattern AI",
    width: int = 1200,
    height: int = 900,
) -> str:
    """
    Gera imagem PNG de preview do molde completo.

    Args:
        pieces: Lista de PatternPiece
        output_path: Caminho do arquivo de saída
        title: Título da imagem
        width: Largura do canvas
        height: Altura do canvas

    Returns:
        Caminho do arquivo gerado
    """
    # Criar canvas branco
    img = Image.new("RGB", (width, height), WHITE)
    draw = ImageDraw.Draw(img)

    # Tentar carregar fonte TrueType
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        font = ImageFont.load_default()

    # Calcular bounding box de todas as peças
    all_points = []
    for piece in pieces:
        if piece.outline:
            for pt in piece.outline:
                all_points.append((float(pt[0]), float(pt[1])))

    if not all_points:
        # Fallback para tamanho mínimo
        min_x, min_y = 0, 0
        max_x, max_y = 50, 70
    else:
        min_x = min(p[0] for p in all_points)
        min_y = min(p[1] for p in all_points)
        max_x = max(p[0] for p in all_points)
        max_y = max(p[1] for p in all_points)

    # Calcular escala para caber no canvas
    content_width = max_x - min_x
    content_height = max_y - min_y
    scale_x = (width - 60) / content_width if content_width > 0 else 10
    scale_y = (height - 60) / content_height if content_height > 0 else 10
    scale = min(scale_x, scale_y, 15)  # Limitar escala máxima

    # Layout em grid para múltiplas peças
    num_pieces = len(pieces)
    cols = 2 if num_pieces > 1 else 1
    rows = (num_pieces + 1) // cols

    cell_width = width // cols
    cell_height = height // rows

    # Desenhar cada peça
    for idx, piece in enumerate(pieces):
        col = idx % cols
        row = idx // cols

        offset_x = col * cell_width + 30
        offset_y = row * cell_height + 30

        # Desenhar peça
        draw_piece_outline(draw, piece, offset_x, offset_y, scale)
        draw_curves(draw, piece, offset_x, offset_y, scale)
        draw_grain_line(draw, piece, offset_x, offset_y, scale)
        draw_notches(draw, piece, offset_x, offset_y, scale)
        draw_dimensions(draw, piece, offset_x, offset_y, scale, font)
        draw_label(draw, piece, offset_x, offset_y, font)

    # Salvar imagem
    output_path = Path(output_path)
    img.save(output_path, "PNG")

    return str(output_path)
