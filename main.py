"""
Fashion Pattern AI — API FastAPI

Sistema de Modelagem Industrial com Visão Computacional.
Recebe imagem de pessoa vestida + medidas, exporta molde PDF 1:1.
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.background import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import json
import asyncio
import shutil
from pathlib import Path

from src.models.measurements import BodyMeasurements
from src.models.enums import FabricType, FitLevel, GarmentType
from src.vision.landmark_extractor import LandmarkExtractor
from src.vision.garment_classifier import GarmentClassifier, GarmentFeatures
from src.pattern.diagram_builder import DiagramBuilder
from src.pattern.ease_calculator import apply_ease_to_pieces
from src.pattern.grading import grade_piece
from src.export.pdf_generator import export_to_pdf

app = FastAPI(title="Fashion Pattern AI", version="1.0")

# CORS para desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0"}


@app.post("/generate-pattern", response_class=FileResponse)
async def generate_pattern(
    image: UploadFile = File(..., description="Imagem da pessoa vestida"),
    busto: float = Form(..., description="Circunferência do busto (cm)", ge=60, le=160),
    cintura: float = Form(..., description="Circunferência da cintura (cm)"),
    quadril: float = Form(..., description="Circunferência do quadril (cm)"),
    altura: float = Form(..., description="Altura total (cm)"),
    fabric_type: str = Form(..., description="Tipo de tecido", pattern="^(plano|malha)$"),
    fit_level: str = Form(..., description="Nível de caimento", pattern="^(justo|padrao|amplo)$"),
    size: str = Form(..., description="Tamanho (ex: 38, 40, M)"),
    reference: str = Form(..., description="Referência do modelo (ex: BL-001)"),
    override_features: str | None = Form(None, description="JSON de GarmentFeatures (opcional)"),
):
    """
    Gera molde industrial a partir de imagem e medidas.

    Fluxo:
      1. Salvar imagem em temp file
      2. Extrair landmarks anatômicos
      3. Classificar características da peça
      4. Construir diagrama 2D
      5. Aplicar folga
      6. Aplicar gradação (se necessário)
      7. Exportar PDF
    """
    # Validar enums
    try:
        fabric = FabricType(fabric_type)
        fit = FitLevel(fit_level)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Valor inválido: {e}")

    # Criar diretório temporário
    tmpdir = Path(tempfile.mkdtemp())

    try:
        # 1. Salvar imagem
        image_path = tmpdir / f"upload_{image.filename}"
        with open(image_path, "wb") as f:
            content = await image.read()
            f.write(content)

        # 2. Extrair landmarks (opcional - não usado no cálculo atual)
        try:
            extractor = LandmarkExtractor()
            landmarks = extractor.extract(image_path)
        except ValueError as e:
            # Landmarks falharam, continuar sem eles
            landmarks = None

        # 3. Classificar peça
        classifier = GarmentClassifier()

        # Parse override_features se fornecido
        override = None
        if override_features:
            try:
                data = json.loads(override_features)
                override = GarmentFeatures(
                    fabric_type=FabricType(data["fabric_type"]),
                    garment_type=GarmentType(data["garment_type"]),
                    has_sleeves=data["has_sleeves"],
                    neckline=data["neckline"],
                    has_dart=data["has_dart"],
                )
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                raise HTTPException(status_code=400, detail=f"override_features inválido: {e}")

        features = classifier.classify(image_path, override)

        # 4. Criar medidas
        try:
            measurements = BodyMeasurements(
                busto=busto,
                cintura=cintura,
                quadril=quadril,
                altura=altura,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # 5. Construir diagrama
        builder = DiagramBuilder(measurements, features)
        pieces = builder.build_all()

        # 6. Aplicar folga
        pieces = apply_ease_to_pieces(pieces, fabric, fit, features.has_sleeves)

        # 7. Aplicar gradação (se size diferir do base)
        # Tamanho base assumido como "40"
        size_delta = _calculate_size_delta(size)
        if size_delta != 0:
            pieces = [grade_piece(p, size_delta) for p in pieces]

        # Atualizar metadados das peças
        for piece in pieces:
            piece.size = size
            piece.reference = f"{reference}-{piece.name[0].upper()}"

        # 8. Exportar PDF
        output_path = tmpdir / "molde.pdf"
        export_to_pdf(pieces, str(output_path), title=f"{reference} - {size}")

        # 9. Retornar FileResponse com cleanup no background
        background = BackgroundTasks()
        background.add_task(_cleanup_temp, tmpdir)
        return FileResponse(
            str(output_path),
            media_type="application/pdf",
            filename=f"molde_{reference}_{size}.pdf",
            background=background
        )
    except Exception:
        # Limpar diretório em caso de erro
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise


def _calculate_size_delta(size: str) -> int:
    """
    Calcula delta de tamanho em relação ao base (40).

    Ex: 42 → +1, 38 → -1, 44 → +2
    """
    # Mapeamento simples de tamanhos numéricos
    size_map = {
        "36": -2,
        "38": -1,
        "40": 0,
        "42": 1,
        "44": 2,
        "46": 3,
        "48": 4,
    }
    return size_map.get(size, 0)


async def _cleanup_temp(tmpdir: Path):
    """Limpa diretório temporário após resposta."""
    await asyncio.sleep(0.1)  # Aguarda resposta ser enviada
    shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
