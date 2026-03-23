"""
Construtor de diagrama 2D para moldes industriais.
Converte medidas corporais em pontos 2D do molde (frente, costas, manga).
"""
from src.models.measurements import BodyMeasurements
from src.models.pattern_piece import PatternPiece, Point2D
from src.vision.garment_classifier import GarmentFeatures


class DiagramBuilder:
    """
    Constrói peças de molde 2D a partir de medidas e características.

    FÓRMULAS OBRIGATÓRIAS:
      largura_frente  = busto / 4 + 1.0          (cm)
      largura_costas  = busto / 4 - 1.0          (cm)
      caimento_ombro  = 1.5                       (cm)
      altura_cava     = busto / 8 + 3.0           (cm)

    SISTEMA DE COORDENADAS:
      Origem (0,0) = canto superior esquerdo
      X cresce para direita
      Y cresce para baixo
    """

    def __init__(self, measurements: BodyMeasurements, features: GarmentFeatures):
        self.m = measurements
        self.f = features
        self._validate()

    def _validate(self):
        """Verificar que todas as medidas necessárias estão presentes."""
        required = ["busto", "cintura", "quadril", "altura"]
        for field in required:
            if getattr(self.m, field) is None:
                raise ValueError(f"Medida obrigatória faltando: {field}")

    def build_all(self) -> list[PatternPiece]:
        """Retorna lista com todas as peças do modelo."""
        pieces = [self.build_front(), self.build_back()]
        if self.f.has_sleeves:
            pieces.append(self.build_sleeve())
        return pieces

    def build_front(self) -> PatternPiece:
        """
        Constrói o molde da frente.

        Retorna PatternPiece com outline da frente.
        """
        busto = self.m.busto
        largura = busto / 4 + 1.0  # fórmula obrigatória
        altura_cava = busto / 8 + 3.0  # fórmula obrigatória

        # Calcular altura do molde baseado na medida de tronco ou proporção
        altura_tronco = self.m.comprimento_tronco or (busto * 0.4)

        # Pontos do outline (sentido horário, começando do decote)
        # Decote frente: largura ~7cm, profundidade ~9cm
        neck_width = 7.0
        neck_depth = 9.0

        # Ombro frente: fica 1.5cm ACIMA do ombro das costas (ergonomia)
        shoulder_slope = 1.5  # cm de queda do ombro
        shoulder_length = largura * 0.25  # ~25% da largura

        # Construir outline ponto por ponto
        outline: list[Point2D] = []

        # 1. Decote centro (topo)
        outline.append((0.0, 0.0))

        # 2. Decote curva até ombro
        outline.append((neck_width, 0.0))  # lado do decote
        outline.append((neck_width, -neck_depth))  # curva do decote (y negativo = acima)

        # 3. Ombro
        shoulder_x = neck_width + shoulder_length
        shoulder_y = shoulder_slope  # ombro desce 1.5cm
        outline.append((shoulder_x, shoulder_y))

        # 4. Cava (curva até lateral)
        # Cava começa no ombro e desce até axila
        armhole_depth = altura_cava
        armhole_width = largura * 0.15  # ~15% da largura

        # Ponta da cava
        outline.append((largura, armhole_depth))

        # 5. Lateral (até cintura)
        waist_y = altura_tronco * 0.5  # cintura na metade do tronco
        outline.append((largura, waist_y))

        # 6. Cintura até quadril
        hip_y = altura_tronco * 0.75
        outline.append((largura, hip_y))

        # 7. Barra inferior
        hem_y = altura_tronco
        outline.append((largura, hem_y))

        # 8. Centro frente (volta para origem)
        outline.append((0.0, hem_y))
        outline.append((0.0, 0.0))

        # Notches: pontos de encontro nas cavas (mínimo 2 por cava)
        notches = [
            (shoulder_x, shoulder_y),  # topo da cava
            (largura, armhole_depth),  # fundo da cava
        ]

        # Dart apex: se has_dart=True
        dart_apex = None
        if self.f.has_dart:
            # Posição: centro do busto, ~2cm antes do ápice real
            bust_center_x = largura / 2
            bust_apex_y = armhole_depth + 5.0
            dart_apex = (bust_center_x, bust_apex_y)

        # Grain line: linha vertical no centro da peça
        grain_line = (
            (largura / 2, 5.0),
            (largura / 2, hem_y - 5.0)
        )

        return PatternPiece(
            name="Frente",
            size="",  # será preenchido depois
            reference="",
            cut_quantity=2,
            outline=outline,
            grain_line=grain_line,
            seam_allowance_cm=1.0,
            notches=notches,
            dart_apex=dart_apex,
            instructions="Cortar 2x no dobro",
        )

    def build_back(self) -> PatternPiece:
        """
        Constrói o molde das costas.

        Retorna PatternPiece com outline das costas.
        """
        busto = self.m.busto
        largura = busto / 4 - 1.0  # fórmula obrigatória (2cm menos que frente)
        altura_cava = busto / 8 + 3.0  # fórmula obrigatória

        altura_tronco = self.m.comprimento_tronco or (busto * 0.4)

        # Decote costas: mais estreito e menos profundo que frente
        neck_width = 6.5
        neck_depth = 3.0  # menos profundo que frente

        # Ombro costas: 1.5cm abaixo do ombro frente
        shoulder_slope = 1.5
        shoulder_length = largura * 0.25

        outline: list[Point2D] = []

        # 1. Decote centro
        outline.append((0.0, 0.0))

        # 2. Decote curva
        outline.append((neck_width, 0.0))
        outline.append((neck_width, -neck_depth))

        # 3. Ombro
        shoulder_x = neck_width + shoulder_length
        shoulder_y = shoulder_slope
        outline.append((shoulder_x, shoulder_y))

        # 4. Cava
        armhole_depth = altura_cava
        outline.append((largura, armhole_depth))

        # 5. Lateral até cintura
        waist_y = altura_tronco * 0.5
        outline.append((largura, waist_y))

        # 6. Cintura até quadril
        hip_y = altura_tronco * 0.75
        outline.append((largura, hip_y))

        # 7. Barra
        hem_y = altura_tronco
        outline.append((largura, hem_y))

        # 8. Centro costas (volta para origem)
        outline.append((0.0, hem_y))
        outline.append((0.0, 0.0))

        notches = [
            (shoulder_x, shoulder_y),
            (largura, armhole_depth),
        ]

        grain_line = (
            (largura / 2, 5.0),
            (largura / 2, hem_y - 5.0)
        )

        return PatternPiece(
            name="Costas",
            size="",
            reference="",
            cut_quantity=2,
            outline=outline,
            grain_line=grain_line,
            seam_allowance_cm=1.0,
            notches=notches,
            dart_apex=None,  # costas geralmente sem pence
            instructions="Cortar 2x no dobro",
        )

    def build_sleeve(self) -> PatternPiece:
        """
        Constrói o molde da manga.

        Fórmula manga: altura_manga = altura_cava * 1.3
        """
        busto = self.m.busto
        altura_cava = busto / 8 + 3.0
        altura_manga = altura_cava * 1.3  # fórmula obrigatória

        # Largura da manga: baseada na circunferência do braço
        # Proporção industrial: ~40% do busto / 4
        sleeve_width = (busto / 4) * 0.4 * 2  # manga completa

        # Comprimento da manga: do ombro ao cotovelo/punho
        sleeve_length = self.m.altura * 0.25  # ~25% da altura total

        outline: list[Point2D] = []

        # 1. Topo centro da manga (cabeça)
        crown_height = altura_manga * 0.3
        outline.append((sleeve_width / 2, 0.0))

        # 2. Curva da cabeça da manga (direita)
        outline.append((sleeve_width, -crown_height / 2))

        # 3. Lateral direita (até punho)
        outline.append((sleeve_width, sleeve_length))

        # 4. Punho (mais estreito)
        cuff_width = sleeve_width * 0.7
        outline.append((cuff_width, sleeve_length))

        # 5. Lateral esquerda
        outline.append((0.0, sleeve_length))

        # 6. Curva da cabeça (esquerda)
        outline.append((0.0, -crown_height / 2))

        # 7. Volta para topo
        outline.append((sleeve_width / 2, 0.0))

        # Notches: topo e base da cava
        notches = [
            (sleeve_width / 2, crown_height),  # topo
            (0.0, 0.0),  # base esquerda
            (sleeve_width, 0.0),  # base direita
        ]

        # Grain line: vertical no centro
        grain_line = (
            (sleeve_width / 2, 5.0),
            (sleeve_width / 2, sleeve_length - 5.0)
        )

        return PatternPiece(
            name="Manga",
            size="",
            reference="",
            cut_quantity=2,
            outline=outline,
            grain_line=grain_line,
            seam_allowance_cm=1.0,
            notches=notches,
            dart_apex=None,
            instructions="Cortar 2x",
        )
