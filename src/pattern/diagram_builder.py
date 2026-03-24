"""
Construtor de diagrama 2D para moldes industriais.
Converte medidas corporais em pontos 2D do molde (frente, costas, manga).
"""
from src.models.measurements import BodyMeasurements
from src.models.pattern_piece import PatternPiece, Point2D
from src.vision.garment_classifier import GarmentFeatures
from src.models.enums import GarmentType


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

    def __init__(self, measurements: BodyMeasurements, features: GarmentFeatures, reference: str = "", size: str = ""):
        self.m = measurements
        self.f = features
        self.reference = reference
        self.size = size
        self._validate()

    def _validate(self):
        """Verificar que todas as medidas necessárias estão presentes."""
        required = ["busto", "cintura", "quadril", "altura"]
        for field in required:
            if getattr(self.m, field) is None:
                raise ValueError(f"Medida obrigatória faltando: {field}")

    def build_all(self) -> list[PatternPiece]:
        """Retorna lista com todas as peças do modelo."""
        bottom_types = [
            GarmentType.CALCA, 
            GarmentType.SAIA, 
            GarmentType.SHORT, 
            GarmentType.BERMUDA
        ]
        
        is_bottom = self.f.garment_type in bottom_types
        
        if is_bottom:
            pieces = [self.build_bottom_front(), self.build_bottom_back()]
        else:
            # Frente Industrial (Dividida se for camisa)
            pieces = [self.build_front(), self.build_back()]
            
            if self.f.has_sleeves:
                pieces.append(self.build_sleeve())
                if self.f.has_cuffs:
                    pieces.extend(self.build_cuffs())
            
            if self.f.has_collar:
                pieces.extend(self.build_collar())
                
        return pieces

    def build_front(self) -> PatternPiece:
        """
        Constrói o molde da frente (Industrial Shirt style) com cotas.
        """
        busto = self.m.busto
        largura_base = busto / 4 + 1.0
        placket = 3.0 if self.f.has_collar else 0.0
        largura = largura_base + placket

        neck_width = 8.0
        neck_depth = 10.0
        shoulder_length = 10.0
        armhole_h = busto / 8 + 3.0  # fórmula industrial

        altura_tronco = self.m.comprimento_tronco or (busto * 0.45)
        hem_y = altura_tronco
        shoulder_x = neck_width + shoulder_length

        outline = [
            (-placket, 0.0), (neck_width, 0.0), (neck_width, -neck_depth),
            (shoulder_x, 1.5), (largura, armhole_h), (largura, hem_y),
            (-placket, hem_y), (-placket, 0.0)
        ]

        dims = [
            {"label": f"{largura:.1f}cm", "start": (-placket, hem_y + 3), "end": (largura, hem_y + 3), "type": "h"},
            {"label": "8cm", "start": (0, -2), "end": (neck_width, -2), "type": "h"},
            {"label": "10cm", "start": (neck_width, -neck_depth - 2), "end": (shoulder_x, -neck_depth - 2), "type": "h"},
            {"label": "29cm", "start": (largura + 3, 0), "end": (largura + 3, armhole_h), "type": "v"},
            {"label": f"{hem_y:.1f}cm", "start": (-placket - 3, 0), "end": (-placket - 3, hem_y), "type": "v"},
        ]

        return PatternPiece(
            name="Frente (Esq/Dir)",
            size=self.size, reference=self.reference, cut_quantity=2,
            outline=outline, dimensions=dims,
            grain_line=((largura/2, 5.0), (largura/2, hem_y - 5.0)),
            seam_allowance_cm=1.0, instructions="Cortar 2x (par espelhado)",
        )

    def build_back(self) -> PatternPiece:
        """
        Constrói o molde das costas (Industrial Shirt style) com cotas.
        """
        busto = self.m.busto
        largura = busto / 4 - 1.0
        
        neck_width = 8.0
        neck_depth = 3.0
        shoulder_length = 10.0
        armhole_h = 19.0
        
        altura_tronco = self.m.comprimento_tronco or (busto * 0.45)
        hem_y = altura_tronco
        shoulder_x = neck_width + shoulder_length

        outline = [
            (0.0, 0.0), (neck_width, 0.0), (neck_width, -neck_depth),
            (shoulder_x, 1.5), (largura, armhole_h), (largura, hem_y),
            (0.0, hem_y), (0.0, 0.0)
        ]

        dims = [
            {"label": f"{largura:.1f}cm", "start": (0, hem_y + 3), "end": (largura, hem_y + 3), "type": "h"},
            {"label": "8cm", "start": (0, -2), "end": (neck_width, -2), "type": "h"},
            {"label": "19cm", "start": (largura + 3, 0), "end": (largura + 3, armhole_h), "type": "v"},
            {"label": f"{hem_y:.1f}cm", "start": (-3, 0), "end": (-3, hem_y), "type": "v"},
        ]

        return PatternPiece(
            name="Costas",
            size=self.size, reference=self.reference, cut_quantity=1,
            outline=outline, dimensions=dims,
            grain_line=((largura/2, 5.0), (largura/2, hem_y - 5.0)),
            seam_allowance_cm=1.0, instructions="Cortar 1x no dobro (centro costas)",
        )

    def build_sleeve(self) -> PatternPiece:
        """
        Constrói o molde da manga com cotas.
        """
        busto = self.m.busto
        sleeve_width = 25.0 # Seguir referência
        sleeve_length = 57.0 # Seguir referência
        crown_h = 17.0

        outline = [
            (sleeve_width/2, 0.0), (sleeve_width, crown_h),
            (sleeve_width, sleeve_length), (0.0, sleeve_length),
            (0.0, crown_h), (sleeve_width/2, 0.0)
        ]

        dims = [
            {"label": "25cm", "start": (0, sleeve_length + 3), "end": (sleeve_width, sleeve_length + 3), "type": "h"},
            {"label": "57cm", "start": (sleeve_width + 3, 0), "end": (sleeve_width + 3, sleeve_length), "type": "v"},
            {"label": "17cm", "start": (-3, 0), "end": (-3, crown_h), "type": "v"},
        ]

        return PatternPiece(
            name="Manga",
            size=self.size, reference=self.reference, cut_quantity=2,
            outline=outline, dimensions=dims,
            grain_line=((sleeve_width/2, 5.0), (sleeve_width/2, sleeve_length - 5.0)),
            seam_allowance_cm=1.0, instructions="Cortar 2x",
        )

    def build_bottom_front(self) -> PatternPiece:
        """
        Constrói o molde da frente de calça/short/saia.
        """
        quadril = self.m.quadril
        altura = self.m.altura
        
        # Largura base (1/4 do quadril)
        largura = quadril / 4
        
        # Comprimento baseado no tipo
        if self.f.garment_type == GarmentType.CALCA:
            comprimento = altura * 0.6  # ~60% da altura total
        elif self.f.garment_type == GarmentType.BERMUDA:
            comprimento = altura * 0.35
        elif self.f.garment_type == GarmentType.SHORT:
            comprimento = altura * 0.25
        else: # SAIA
            comprimento = altura * 0.35
            
        altura_gancho = quadril / 4  # fórmula básica do gancho
        
        # Geometria simplificada (retângulo com curva de gancho)
        outline: list[Point2D] = []
        
        # 1. Cintura centro frente
        outline.append((0.0, 0.0))
        
        # 2. Cintura lateral
        outline.append((largura, 0.0))
        
        # 3. Lateral até barra
        outline.append((largura, comprimento))
        
        # 4. Barra centro
        outline.append((0.0, comprimento))
        
        # 5. Gancho/Entrepernas se não for saia
        if self.f.garment_type != GarmentType.SAIA:
            # Curva do gancho aproximada
            outline.insert(4, (largura * 0.1, comprimento)) # Entrepernas
            outline.insert(5, (largura * 0.15, altura_gancho)) # Curva gancho
            
        outline.append((0.0, 0.0)) # Fechar
        
        notches = [(largura, altura_gancho)]
        grain_line = ((largura / 2, 5.0), (largura / 2, comprimento - 5.0))
        
        return PatternPiece(
            name="Frente (Baixo)",
            size=self.size,
            reference=self.reference,
            cut_quantity=2,
            outline=outline,
            grain_line=grain_line,
            seam_allowance_cm=1.0,
            notches=notches,
            dart_apex=None,
            instructions="Cortar 2x",
        )

    def build_bottom_back(self) -> PatternPiece:
        """
        Constrói o molde das costas de calça/short/saia.
        Costas é ligeiramente mais larga e alta no gancho.
        """
        quadril = self.m.quadril
        altura = self.m.altura
        
        largura = quadril / 4 + 2.0  # costas mais largas
        
        if self.f.garment_type == GarmentType.CALCA:
            comprimento = altura * 0.6
        elif self.f.garment_type == GarmentType.BERMUDA:
            comprimento = altura * 0.35
        elif self.f.garment_type == GarmentType.SHORT:
            comprimento = altura * 0.25
        else: # SAIA
            comprimento = altura * 0.35
            
        altura_gancho = quadril / 4
        
        outline: list[Point2D] = []
        
        # 1. Cintura centro costas (mais alto)
        outline.append((0.0, -3.0))
        
        # 2. Cintura lateral
        outline.append((largura, 0.0))
        
        # 3. Lateral até barra
        outline.append((largura, comprimento))
        
        # 4. Barra centro
        outline.append((0.0, comprimento))
        
        if self.f.garment_type != GarmentType.SAIA:
            # Gancho costas (maior)
            outline.insert(4, (largura * 0.2, comprimento))
            outline.insert(5, (largura * 0.25, altura_gancho))
            
        outline.append((0.0, -3.0))
        
        notches = [(largura, altura_gancho)]
        grain_line = ((largura / 2, 5.0), (largura / 2, comprimento - 5.0))
        
        return PatternPiece(
            name="Costas (Baixo)",
            size=self.size,
            reference=self.reference,
            cut_quantity=2,
            outline=outline,
            grain_line=grain_line,
            seam_allowance_cm=1.0,
            notches=notches,
            dart_apex=None,
            instructions="Cortar 2x",
        )

    def build_collar(self) -> list[PatternPiece]:
        """Gera Pé de Gola e Gola Superior."""
        neck_circ = self.m.pescoco or 40.0
        width = neck_circ / 2 + 2.0 # metade + transpasse
        
        # Pé de Gola (Collar Stand)
        stand_outline = [
            (0.0, 0.0), (width, 0.0), (width, 3.5), (0.0, 3.5), (0.0, 0.0)
        ]
        stand = PatternPiece(
            name="Pé de Gola",
            size=self.size,
            reference=self.reference,
            cut_quantity=2,
            outline=stand_outline,
            instructions="Cortar 2x (1 com entretela)"
        )
        
        # Gola (Collar)
        collar_outline = [
            (0.0, 0.0), (width + 1.0, 0.0), (width + 2.5, 6.0), (0.0, 6.0), (0.0, 0.0)
        ]
        collar = PatternPiece(
            name="Gola Superior",
            size=self.size,
            reference=self.reference,
            cut_quantity=2,
            outline=collar_outline,
            instructions="Cortar 2x"
        )
        return [stand, collar]

    def build_cuffs(self) -> list[PatternPiece]:
        """Gera Punhos."""
        width = 25.0
        height = 7.0
        outline = [(0.0, 0.0), (width, 0.0), (width, height), (0.0, height), (0.0, 0.0)]
        return [PatternPiece(
            name="Punho",
            size=self.size,
            reference=self.reference,
            cut_quantity=2,
            outline=outline,
            instructions="Cortar 2x"
        )]
