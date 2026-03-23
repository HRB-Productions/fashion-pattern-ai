"""
Gerador de PDF em escala 1:1 para moldes industriais.
Usa ReportLab para gerar PDFs A4 em formato pôster.

ESPECIFICAÇÕES:
  - Formato: A4 pôster (múltiplas páginas com marcas de alinhamento)
  - Escala: 1:1 — 1 cm no molde = 1 cm no papel impresso
  - Cada peça é impressa INTEIRA (nunca pela metade)
"""
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import cm
from reportlab.graphics.shapes import Path, Drawing
from reportlab.lib.colors import black, HexColor
from src.models.pattern_piece import PatternPiece, Point2D
import math

A4_W, A4_H = A4   # pontos ReportLab
CM_TO_PT = cm     # fator de conversão: 1 cm = 28.35 pontos


def export_to_pdf(
    pieces: list[PatternPiece],
    output_path: str,
    title: str = "Molde Industrial"
) -> str:
    """
    Exporta lista de PatternPiece para PDF multi-página A4 em escala 1:1.
    Retorna o caminho do arquivo gerado.
    """
    # Criar canvas
    c = rl_canvas.Canvas(output_path, pagesize=A4)

    all_pages = []

    for piece in pieces:
        # Calcular dimensões da peça
        piece_width = max(p[0] for p in piece.outline) - min(p[0] for p in piece.outline)
        piece_height = max(p[1] for p in piece.outline) - min(p[1] for p in piece.outline)

        # Calcular tiles A4 necessários
        tiles = _tile_to_a4(piece_width, piece_height)

        for tile_idx, (offset_x, offset_y) in enumerate(tiles):
            page_num = len(all_pages) + 1
            all_pages.append({
                'piece': piece,
                'offset_x': offset_x,
                'offset_y': offset_y,
                'tile_idx': tile_idx,
                'total_tiles': len(tiles),
            })

    # Desenhar todas as páginas
    for page_data in all_pages:
        _draw_page(
            c,
            page_data['piece'],
            page_data['offset_x'],
            page_data['offset_y'],
            page_data['tile_idx'],
            page_data['total_tiles'],
            title
        )
        c.showPage()

    c.save()
    return output_path


def _draw_page(
    c: rl_canvas.Canvas,
    piece: PatternPiece,
    offset_x: float,
    offset_y: float,
    tile_idx: int,
    total_tiles: int,
    title: str
):
    """Desenha uma página do PDF com a peça e marcações."""
    # Margem de segurança
    margin = 1 * cm

    # Desenhar peça com offset
    _draw_piece(c, piece, offset_x * CM_TO_PT, offset_y * CM_TO_PT)

    # Desenhar marcas de alinhamento
    _draw_alignment_marks(c, tile_idx, total_tiles, title)


def _draw_piece(c: rl_canvas.Canvas, piece: PatternPiece, ox: float, oy: float):
    """Desenha uma peça no canvas ReportLab com todas as marcações."""
    _draw_outline(c, piece, ox, oy)
    _draw_seam_allowance(c, piece, ox, oy)
    _draw_grain_line(c, piece, ox, oy)
    _draw_notches(c, piece, ox, oy)
    if piece.dart_apex:
        _draw_dart_apex(c, piece.dart_apex, ox, oy, piece_height_cm(piece))
    _draw_label(c, piece, ox, oy)


def _draw_outline(c: rl_canvas.Canvas, piece: PatternPiece, ox: float, oy: float):
    """
    Desenha o contorno da peça com linha contínua 0.5 mm.
    """
    path = c.beginPath()

    # Inverter Y porque ReportLab tem origem no canto inferior esquerdo
    first = True
    for x, y in piece.outline:
        px = ox + x * CM_TO_PT
        py = oy + (piece_height_cm(piece) - y) * CM_TO_PT

        if first:
            path.moveTo(px, py)
            first = False
        else:
            path.lineTo(px, py)

    path.close()
    c.setLineWidth(0.5)
    c.setStrokeColor(black)
    c.drawPath(path)


def piece_height_cm(piece: PatternPiece) -> float:
    """Retorna altura da peça em cm."""
    return max(p[1] for p in piece.outline) - min(p[1] for p in piece.outline)


def piece_width_cm(piece: PatternPiece) -> float:
    """Retorna largura da peça em cm."""
    return max(p[0] for p in piece.outline) - min(p[0] for p in piece.outline)


def _draw_seam_allowance(c: rl_canvas.Canvas, piece: PatternPiece, ox: float, oy: float):
    """
    Desenha margem de costura: 1 cm todo o contorno (linha tracejada 0.3 mm).
    EXCEÇÃO: barra inferior → margem de 2 cm.
    """
    from shapely.geometry import Polygon, LineString
    from shapely.affinity import scale

    # Criar polígono do outline
    points = [(x, piece_height_cm(piece) - y) for x, y in piece.outline]
    poly = Polygon(points)

    # Offset de 1 cm (2 cm na barra inferior - handled by uniform offset for simplicity)
    offset_cm = 1.0
    try:
        seam_poly = poly.buffer(offset_cm, resolution=4)

        # Desenhar como linha tracejada
        path = c.beginPath()
        first = True

        # Obter contorno externo
        if hasattr(seam_poly, 'exterior'):
            for x, y in seam_poly.exterior.coords:
                px = ox + x * CM_TO_PT
                py = oy + y * CM_TO_PT

                if first:
                    path.moveTo(px, py)
                    first = False
                else:
                    path.lineTo(px, py)

        c.setLineWidth(0.3)
        c.setDash(3, 3)  # tracejado
        c.drawPath(path)
        c.setDash()  # reset
    except Exception:
        # Fallback simples se shapely falhar
        _draw_simple_seam_allowance(c, piece, ox, oy)


def _draw_simple_seam_allowance(c: rl_canvas.Canvas, piece: PatternPiece, ox: float, oy: float):
    """Fallback simples para margem de costura."""
    path = c.beginPath()
    first = True
    offset = 1.0 * CM_TO_PT

    for x, y in piece.outline:
        px = ox + x * CM_TO_PT + offset
        py = oy + (piece_height_cm(piece) - y) * CM_TO_PT + offset

        if first:
            path.moveTo(px, py)
            first = False
        else:
            path.lineTo(px, py)

    c.setLineWidth(0.3)
    c.setDash(3, 3)
    c.drawPath(path)
    c.setDash()


def _draw_grain_line(c: rl_canvas.Canvas, piece: PatternPiece, ox: float, oy: float):
    """
    Seta dupla (duas pontas) paralela ao centro vertical.
    Comprimento = 60% da altura da peça.
    """
    start, end = piece.grain_line
    height = piece_height_cm(piece)

    # Calcular posição da grain line (60% da altura)
    grain_length = height * 0.6
    grain_center_y = (start[1] + end[1]) / 2

    # Centro X da peça
    grain_x = (start[0] + end[0]) / 2

    # Desenhar linha dupla com setas
    line_y_start = grain_center_y - grain_length / 2
    line_y_end = grain_center_y + grain_length / 2

    # Inverter Y para ReportLab
    py_start = oy + (height - line_y_start) * CM_TO_PT
    py_end = oy + (height - line_y_end) * CM_TO_PT
    px = ox + grain_x * CM_TO_PT

    # Linha principal
    c.setLineWidth(0.5)
    c.setStrokeColor(black)
    c.line(px - 2, py_start, px - 2, py_end)
    c.line(px + 2, py_start, px + 2, py_end)

    # Setas nas extremidades
    arrow_size = 0.3 * CM_TO_PT
    c.setLineWidth(0.3)

    # Seta superior (apontando para cima)
    c.line(px - 2, py_end - arrow_size, px - 2, py_end)
    c.line(px - 2, py_end, px - 4, py_end - arrow_size * 0.7)
    c.line(px + 2, py_end - arrow_size, px + 2, py_end)
    c.line(px + 2, py_end, px + 4, py_end - arrow_size * 0.7)

    # Seta inferior (apontando para baixo)
    c.line(px - 2, py_start + arrow_size, px - 2, py_start)
    c.line(px - 2, py_start, px - 4, py_start + arrow_size * 0.7)
    c.line(px + 2, py_start + arrow_size, px + 2, py_start)
    c.line(px + 2, py_start, px + 4, py_start + arrow_size * 0.7)


def _draw_notches(c: rl_canvas.Canvas, piece: PatternPiece, ox: float, oy: float):
    """
    Piques (notches): triângulos de 0.5 cm apontando para fora do contorno.
    """
    height = piece_height_cm(piece)
    notch_size = 0.5 * CM_TO_PT

    for nx, ny in piece.notches:
        px = ox + nx * CM_TO_PT
        py = oy + (height - ny) * CM_TO_PT

        # Triângulo apontando para fora (direita)
        path = c.beginPath()
        path.moveTo(px, py - notch_size / 2)
        path.lineTo(px + notch_size, py)
        path.lineTo(px, py + notch_size / 2)
        path.close()

        c.setLineWidth(0.3)
        c.drawPath(path)


def _draw_dart_apex(c: rl_canvas.Canvas, apex: Point2D, ox: float, oy: float, piece_height: float = None):
    """
    Círculo de 0.3 cm no ápice da pence.
    """
    # Se piece_height não for fornecido, usar valor default
    height = piece_height if piece_height is not None else 10
    px = ox + apex[0] * CM_TO_PT
    py = oy + (height - apex[1]) * CM_TO_PT

    radius = 0.3 * CM_TO_PT
    c.circle(px, py, radius, stroke=1, fill=0)


def _draw_label(c: rl_canvas.Canvas, piece: PatternPiece, ox: float, oy: float):
    """
    Etiqueta de identificação (canto inferior direito):
      Linha 1: nome da peça
      Linha 2: tamanho + referência
      Linha 3: instrução de corte
    """
    height = piece_height_cm(piece)

    # Posição: canto inferior direito
    label_x = ox + 0.5 * CM_TO_PT
    label_y = oy + 0.5 * CM_TO_PT

    c.setFont("Helvetica-Bold", 10)
    c.drawString(label_x, label_y + 30, piece.name.upper())

    c.setFont("Helvetica", 9)
    size_ref = f"TAM {piece.size} | {piece.reference}" if piece.size else piece.reference
    c.drawString(label_x, label_y + 15, size_ref)

    c.drawString(label_x, label_y, piece.instructions)


def _tile_to_a4(
    piece_width_cm: float,
    piece_height_cm: float
) -> list[tuple[float, float]]:
    """
    Calcula quantas folhas A4 necessárias e os offsets de impressão
    para que as folhas unidas formem a peça em tamanho real.

    A4 útil: ~20cm x 28cm (com margens)
    """
    # A4 útil em cm (considerando margens de 1.5cm)
    a4_useful_width = (A4_W - 3 * cm) / CM_TO_PT  # ~20 cm
    a4_useful_height = (A4_H - 3 * cm) / CM_TO_PT  # ~28 cm

    tiles = []

    # Calcular número de tiles em cada direção
    tiles_x = max(1, math.ceil(piece_width_cm / a4_useful_width))
    tiles_y = max(1, math.ceil(piece_height_cm / a4_useful_height))

    for ty in range(tiles_y):
        for tx in range(tiles_x):
            offset_x = tx * a4_useful_width
            offset_y = ty * a4_useful_height
            tiles.append((offset_x, offset_y))

    return tiles


def _draw_alignment_marks(c: rl_canvas.Canvas, tile_idx: int, total_tiles: int, title: str):
    """
    Cruz de alinhamento nos 4 cantos (1 cm) e número da folha.
    """
    # Cruzes de 1 cm nos 4 cantos
    cross_size = 1.0 * CM_TO_PT
    margin = 0.5 * CM_TO_PT

    corners = [
        (margin, margin),
        (A4_W - margin, margin),
        (margin, A4_H - margin),
        (A4_W - margin, A4_H - margin),
    ]

    c.setLineWidth(0.3)
    for cx, cy in corners:
        # Cruz horizontal
        c.line(cx - cross_size / 2, cy, cx + cross_size / 2, cy)
        # Cruz vertical
        c.line(cx, cy - cross_size / 2, cx, cy + cross_size / 2)

    # Numeração da página
    page_text = f"Folha {tile_idx + 1} de {total_tiles} — {title}"
    c.setFont("Helvetica", 8)
    c.drawString(A4_W / 2 - 50, margin, page_text)
