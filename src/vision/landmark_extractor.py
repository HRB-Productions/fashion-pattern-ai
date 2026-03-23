"""
Extrator de pontos anatômicos usando MediaPipe Pose.
Mapeia landmarks do MediaPipe para pontos têxteis industriais.

Usa a API moderna do MediaPipe (0.10+): mp.tasks.vision
"""
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import cv2
import numpy as np
from pathlib import Path
import tempfile


class LandmarkExtractor:
    """
    Extrai landmarks anatômicos de uma imagem usando MediaPipe Pose.

    Pontos retornados (normalizados 0-1):
      - acromio_esq, acromio_dir
      - axila_esq, axila_dir
      - apex_busto
      - cintura
      - quadril
    """

    def __init__(self, min_confidence: float = 0.6):
        self.min_confidence = min_confidence
        self._landmarker = None

    def _ensure_landmarker(self):
        """Lazy loading do landmarker."""
        if self._landmarker is None:
            try:
                base_options = python.BaseOptions(model_asset_path='pose_landmarker.task')
                options = vision.PoseLandmarkerOptions(
                    base_options=base_options,
                    running_mode=vision.RunningMode.IMAGE,
                    min_pose_detection_confidence=self.min_confidence,
                    min_pose_presence_confidence=self.min_confidence,
                )
                self._landmarker = vision.PoseLandmarker.create_from_options(options)
            except Exception as e:
                # Modelo não disponível, levantar ValueError para o caller continuar sem landmarks
                raise ValueError(f"MediaPipe Pose landmarker não disponível: {e}")

    def extract(self, image_path: str | Path) -> dict[str, tuple[float, float]]:
        """
        Recebe caminho de imagem, retorna dicionário de landmarks normalizados.

        Returns:
            dict com chaves: acromio_esq, acromio_dir, axila_esq, axila_dir,
                            apex_busto, cintura, quadril
            Cada valor é (x_norm, y_norm) em 0-1
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

        # Carregar imagem
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Não foi possível ler a imagem: {image_path}")

        # Converter para RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        self._ensure_landmarker()

        # Criar imagem MediaPipe
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)

        # Detectar pose
        results = self._landmarker.detect(mp_image)

        if not results.poses or len(results.poses) == 0:
            raise ValueError("Pose não detectada com confiança suficiente")

        # Verificar confiança
        pose = results.poses[0]
        if pose.score < self.min_confidence:
            raise ValueError("Pose não detectada com confiança suficiente")

        return self._map_landmarks(pose)

    def _map_landmarks(self, pose) -> dict[str, tuple[float, float]]:
        """
        Converte resultados do MediaPipe para o dicionário padrão do sistema.
        """
        # MediaPipe novo API retorna keypoints diretamente
        keypoints = pose.keypoints

        # Encontrar índices dos landmarks
        # A ordem é: NOSE, LEFT_EYE, ..., LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP, etc.
        # Index 11 = LEFT_SHOULDER, 12 = RIGHT_SHOULDER, 23 = LEFT_HIP, 24 = RIGHT_HIP

        def get_point(idx: int) -> tuple[float, float]:
            if idx < len(keypoints):
                kp = keypoints[idx]
                return (kp.x, kp.y)
            return (0.0, 0.0)

        # Acromios (ombros) - índices 11 e 12
        acromio_esq = get_point(11)
        acromio_dir = get_point(12)

        # Hips para cálculo de axilas e cintura - índices 23 e 24
        left_hip = get_point(23)
        right_hip = get_point(24)

        # Axilas: ponto médio entre shoulder e hip, com offset vertical
        axila_esq = (
            (acromio_esq[0] + left_hip[0]) / 2,
            acromio_esq[1] + 0.15  # offset vertical para baixo
        )
        axila_dir = (
            (acromio_dir[0] + right_hip[0]) / 2,
            acromio_dir[1] + 0.15
        )

        # Apex do busto: ponto médio horizontal entre os hips
        apex_busto = (
            (left_hip[0] + right_hip[0]) / 2,
            (left_hip[1] + right_hip[1]) / 2 + 0.05  # leve offset
        )

        # Cintura: média dos pontos LEFT_HIP e RIGHT_HIP
        cintura = (
            (left_hip[0] + right_hip[0]) / 2,
            (left_hip[1] + right_hip[1]) / 2
        )

        # Quadril: 0.15 abaixo dos pontos de quadril do MediaPipe
        quadril_y = max(left_hip[1], right_hip[1]) + 0.15
        quadril = (
            (left_hip[0] + right_hip[0]) / 2,
            quadril_y
        )

        return {
            "acromio_esq": acromio_esq,
            "acromio_dir": acromio_dir,
            "axila_esq": axila_esq,
            "axila_dir": axila_dir,
            "apex_busto": apex_busto,
            "cintura": cintura,
            "quadril": quadril,
        }

    def close(self):
        """Limpar recursos."""
        if self._landmarker:
            self._landmarker.close()
            self._landmarker = None
