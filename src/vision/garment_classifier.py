"""
Classificador de peças têxteis usando CLIP (open-clip).
Classifica tipo de tecido, tipo de peça, mangas, gola e pences.
"""
from dataclasses import dataclass
from pathlib import Path
from src.models.enums import FabricType, GarmentType

try:
    import torch
    import open_clip
    OPEN_CLIP_AVAILABLE = True
except ImportError:
    OPEN_CLIP_AVAILABLE = False
    torch = None


@dataclass
class GarmentFeatures:
    """Características da peça classificadas."""
    fabric_type: FabricType
    garment_type: GarmentType
    has_sleeves: bool
    neckline: str  # "redondo", "v", "quadrado", "gola_alta", "decote"
    has_dart: bool
    has_collar: bool = False
    has_cuffs: bool = False


class GarmentClassifier:
    """
    Classifica características de peças de vestuário usando CLIP.

    Se CLIP não estiver disponível, usa override_features como fallback.
    """

    # Prompts para classificação de tecido
    FABRIC_PROMPTS = {
        FabricType.PLANO: "a woven fabric garment",
        FabricType.MALHA: "a knit fabric garment",
    }

    # Prompts para tipo de peça
    GARMENT_PROMPTS = {
        GarmentType.BLUSA: "a blouse or shirt",
        GarmentType.VESTIDO: "a dress",
        GarmentType.CALCA: "pants or trousers",
        GarmentType.SAIA: "a skirt",
        GarmentType.CASACO: "a jacket or coat",
        GarmentType.BODY: "a bodysuit",
    }

    # Prompts para gola
    NECKLINE_PROMPTS = {
        "redondo": "a round neckline",
        "v": "a v-neck",
        "quadrado": "a square neckline",
        "gola_alta": "a high neck or turtleneck",
        "decote": "a deep neckline",
    }

    MIN_CONFIDENCE = 0.30

    def __init__(self):
        self._model = None
        self._preprocess = None
        self._tokenizer = None

    def _load_model(self):
        """Carrega modelo CLIP lazy loading."""
        if not OPEN_CLIP_AVAILABLE:
            return

        device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model, self._preprocess, self._tokenizer = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="laion2b_s34b_b79k", device=device
        )

    def classify(
        self,
        image_path: str | Path,
        override_features: GarmentFeatures | None = None
    ) -> GarmentFeatures:
        """
        Classifica características da peça.

        Args:
            image_path: Caminho da imagem da peça
            override_features: Características manuais (fallback)

        Returns:
            GarmentFeatures com todas as características
        """
        if override_features:
            return override_features

        if not OPEN_CLIP_AVAILABLE:
            raise RuntimeError(
                "open-clip-torch não disponível. "
                "Use override_features para fornecer características manualmente."
            )

        if self._model is None:
            self._load_model()

        image_path = Path(image_path)
        image = self._preprocess(image_path).unsqueeze(0)
        device = next(self._model.parameters()).device

        with torch.no_grad():
            image_features = self._model.encode_image(image.to(device))
            image_features = torch.nn.functional.normalize(image_features, dim=-1)

        # Classificar tipo de tecido
        fabric_type = self._classify_with_prompts(
            image_features, self.FABRIC_PROMPTS
        )

        # Classificar tipo de peça
        garment_type = self._classify_with_prompts(
            image_features, self.GARMENT_PROMPTS
        )

        # Classificar mangas (bool)
        sleeve_prompts = {
            True: "a garment with sleeves",
            False: "a sleeveless garment",
        }
        has_sleeves = self._classify_with_prompts(
            image_features, sleeve_prompts
        )

        # Classificar gola
        neckline = self._classify_with_prompts(
            image_features, self.NECKLINE_PROMPTS
        )

        # Classificar pences
        dart_prompts = {
            True: "a garment with darts or princess seams",
            False: "a garment without darts",
        }
        has_dart = self._classify_with_prompts(
            image_features, dart_prompts
        )

        return GarmentFeatures(
            fabric_type=fabric_type,
            garment_type=garment_type,
            has_sleeves=has_sleeves,
            neckline=neckline,
            has_dart=has_dart,
            has_collar=False, # Default to manual for these
            has_cuffs=False
        )

    def _classify_with_prompts(self, image_features, prompts: dict) -> any:
        """
        Classifica usando similaridade de cosine com prompts.
        """
        device = next(self._model.parameters()).device

        # Tokenizar prompts
        text_tokens = list(prompts.keys())
        text_tokens = [prompts[k] for k in text_tokens]

        with torch.no_grad():
            text_features = self._model.encode_text(
                self._tokenizer(text_tokens).to(device)
            )
            text_features = torch.nn.functional.normalize(text_features, dim=-1)

        # Similaridade cosine
        similarities = (image_features @ text_features.T).softmax(dim=-1)

        # Encontrar melhor match
        best_idx = similarities.argmax(dim=-1).item()
        best_key = list(prompts.keys())[best_idx]

        return best_key
