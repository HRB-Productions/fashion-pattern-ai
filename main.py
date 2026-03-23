"""
Fashion Pattern AI — API FastAPI

Sistema de Modelagem Industrial com Visão Computacional.
Recebe imagem(s) de pessoa vestida + tamanho, exporta molde PDF 1:1.
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.background import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import json
import asyncio
import shutil
from pathlib import Path
from typing import Optional

from src.models.measurements import BodyMeasurements
from src.models.enums import FabricType, FitLevel, GarmentType, SizeSystem
from src.models.size_tables import get_size_measurements, is_valid_size, SIZE_TABLES
from src.i18n import get_message
from src.vision.landmark_extractor import LandmarkExtractor
from src.vision.garment_classifier import GarmentClassifier, GarmentFeatures
from src.pattern.diagram_builder import DiagramBuilder
from src.pattern.ease_calculator import apply_ease_to_pieces
from src.pattern.grading import grade_piece
from src.export.pdf_generator import export_to_pdf

app = FastAPI(title="Fashion Pattern AI", version="2.0")

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
    return {"status": "ok", "version": "2.0"}


@app.post("/generate-pattern")
async def generate_pattern(
    front_image: UploadFile = File(..., description="Imagem frontal da pessoa vestida"),
    back_image: Optional[UploadFile] = File(None, description="Imagem posterior (opcional)"),
    size_system: str = Form(..., description="Sistema de tamanhos", pattern="^(BR|US|EU)$"),
    size_label: str = Form(..., description="Tamanho (ex: M, S, 42)"),
    fabric_type: str = Form(..., description="Tipo de tecido", pattern="^(plano|malha)$"),
    fit_level: str = Form(..., description="Nível de caimento", pattern="^(justo|padrao|amplo)$"),
    reference: str = Form(..., description="Referência do modelo (ex: BL-001)"),
    garment_type: Optional[str] = Form(None, description="Tipo de peça (opcional)"),
    has_sleeves: Optional[bool] = Form(None, description="Possui mangas"),
    neckline: Optional[str] = Form(None, description="Tipo de decote"),
    has_dart: Optional[bool] = Form(None, description="Possui pence"),
    language: str = Form("pt-BR", description="Idioma das mensagens"),
):
    """
    Gera molde industrial a partir de imagem(s) e tamanho padronizado.

    Fluxo:
      1. Validar idioma e sistema de tamanhos
      2. Salvar imagem(s) em temp files
      3. Buscar medidas da tabela baseada no tamanho
      4. Extrair landmarks anatômicos (opcional)
      5. Classificar características da peça
      6. Construir diagrama 2D
      7. Aplicar folga
      8. Exportar PDF
      9. Retornar resposta com mensagem localizada
    """
    # Validar idioma
    if language not in ["pt-BR", "en-US", "es-ES"]:
        language = "pt-BR"

    # Validar enums
    try:
        fabric = FabricType(fabric_type)
        fit = FitLevel(fit_level)
        system = SizeSystem(size_system)
    except ValueError as e:
        msg = get_message(language, "invalid_fabric_type") if "fabric" in str(e).lower() else \
              get_message(language, "invalid_fit_level") if "fit" in str(e).lower() else \
              get_message(language, "invalid_size_system")
        raise HTTPException(status_code=400, detail=msg)

    # Validar tamanho
    if not is_valid_size(size_system, size_label):
        msg = get_message(language, "invalid_size")
        raise HTTPException(status_code=400, detail=msg)

    # Validar imagem frontal
    if not front_image.filename or not front_image.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
        msg = get_message(language, "file_not_image")
        raise HTTPException(status_code=400, detail=msg)

    # Criar diretório temporário
    tmpdir = Path(tempfile.mkdtemp())

    try:
        # 1. Salvar imagem frontal
        front_path = tmpdir / f"front_{front_image.filename}"
        with open(front_path, "wb") as f:
            content = await front_image.read()
            f.write(content)

        # 2. Salvar imagem posterior (se fornecida)
        back_path = None
        if back_image:
            back_path = tmpdir / f"back_{back_image.filename}"
            with open(back_path, "wb") as f:
                content = await back_image.read()
                f.write(content)

        # 3. Buscar medidas da tabela
        measurements_data = get_size_measurements(size_system, size_label)
        if not measurements_data:
            msg = get_message(language, "size_not_found")
            raise HTTPException(status_code=400, detail=msg)

        measurements = BodyMeasurements(**measurements_data)

        # 4. Extrair landmarks (opcional)
        try:
            extractor = LandmarkExtractor()
            landmarks = extractor.extract(front_path)
        except ValueError:
            landmarks = None

        # 5. Classificar peça - usar override se fornecido, senão tentar classifier
        features = None

        # Build override from explicit parameters
        if garment_type or has_sleeves is not None or neckline or has_dart is not None:
            features = GarmentFeatures(
                fabric_type=fabric,
                garment_type=GarmentType(garment_type) if garment_type else GarmentType.BLUSA,
                has_sleeves=has_sleeves if has_sleeves is not None else False,
                neckline=neckline if neckline else "redondo",
                has_dart=has_dart if has_dart is not None else False,
            )
        else:
            # Fallback: usar valores padrão se override não fornecido
            features = GarmentFeatures(
                fabric_type=fabric,
                garment_type=GarmentType.BLUSA,
                has_sleeves=False,
                neckline="redondo",
                has_dart=False,
            )

        # 6. Construir diagrama
        builder = DiagramBuilder(measurements, features)
        pieces = builder.build_all()

        # 7. Aplicar folga
        pieces = apply_ease_to_pieces(pieces, fabric, fit, features.has_sleeves)

        # 8. Atualizar metadados das peças
        for piece in pieces:
            piece.size = f"{size_system}:{size_label}"
            piece.reference = f"{reference}-{piece.name[0].upper()}"

        # 9. Exportar PDF
        output_path = tmpdir / "molde.pdf"
        export_to_pdf(pieces, str(output_path), title=f"{reference} - {size_system}:{size_label}")

        # 10. Retornar FileResponse com cleanup no background
        background = BackgroundTasks()
        background.add_task(_cleanup_temp, tmpdir)

        filename = f"molde_{reference}_{size_system}_{size_label}.pdf"
        return FileResponse(
            str(output_path),
            media_type="application/pdf",
            filename=filename,
            background=background,
            headers={
                "X-Pattern-Message": get_message(language, "success"),
                "X-Size-System": size_system,
                "X-Size-Label": size_label,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        # Limpar diretório em caso de erro
        shutil.rmtree(tmpdir, ignore_errors=True)
        msg = get_message(language, "processing_error")
        raise HTTPException(status_code=500, detail=f"{msg}: {str(e)}")


def _calculate_size_delta(size: str) -> int:
    """
    Calcula delta de tamanho em relação ao base (M/40).

    Ex: G/42 → +1, P/38 → -1
    """
    # Maturidade de tamanhos por sistema
    size_map = {
        # BR
        "PP": -2, "P": -1, "M": 0, "G": 1, "GG": 2,
        # US
        "XS": -2, "S": -1, "M": 0, "L": 1, "XL": 2,
        # EU
        "34": -2, "38": -1, "42": 0, "46": 1, "50": 2,
    }
    return size_map.get(size, 0)


async def _cleanup_temp(tmpdir: Path):
    """Limpa diretório temporário após resposta."""
    await asyncio.sleep(0.1)  # Aguarda resposta ser enviada
    shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
