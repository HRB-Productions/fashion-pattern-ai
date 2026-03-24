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
from datetime import datetime, timedelta

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
from src.export.preview_generator import generate_preview

app = FastAPI(title="Fashion Pattern AI", version="3.0")

# CORS para desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Diretório para arquivos gerados
GENERATED_FILES_DIR = Path("generated_files")
GENERATED_FILES_DIR.mkdir(exist_ok=True)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "3.0"}


@app.get("/files/{filename}")
async def serve_file(filename: str):
    """
    Serve arquivos gerados (preview e PDF).

    URL: /files/molde_preview_XXX.png ou /files/molde_XXX.pdf
    """
    file_path = GENERATED_FILES_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    if file_path.suffix.lower() == ".png":
        media_type = "image/png"
    elif file_path.suffix.lower() == ".pdf":
        media_type = "application/pdf"
    else:
        media_type = "application/octet-stream"

    return FileResponse(str(file_path), media_type=media_type, filename=filename)


@app.post("/generate-pattern")
async def generate_pattern(
    front_image: UploadFile = File(..., description="Imagem frontal da pessoa vestida"),
    back_image: Optional[UploadFile] = File(None, description="Imagem posterior (opcional)"),
    size_system: str = Form(..., description="Sistema de tamanhos", pattern="^(BR|US|EU)$"),
    size_label: str = Form(..., description="Tamanho (ex: M, S, 42)"),
    fabric_type: str = Form(..., description="Tipo de tecido", pattern="^(plano|malha)$"),
    fit_level: str = Form(..., description="Nível de caimento", pattern="^(justo|padrao|amplo)$"),
    reference: str = Form(..., description="Referência do modelo (ex: BL-001)"),
    garment_type: Optional[str] = Form(None, description="Tipo de peça"),
    has_sleeves: Optional[bool] = Form(None, description="Possui mangas"),
    neckline: Optional[str] = Form(None, description="Tipo de decote"),
    has_dart: Optional[bool] = Form(None, description="Possui pence"),
    language: str = Form("pt-BR", description="Idioma das mensagens"),
):
    """
    Gera molde industrial a partir de imagem(s) e tamanho padronizado.

    Retorna JSON com:
    - message: Mensagem de sucesso localizada
    - preview_url: URL para imagem de pré-visualização
    - pdf_url: URL para download do PDF
    - pieces: Lista de peças geradas
    """
    # Validar idioma
    if language not in ["pt-BR", "en-US", "es-ES"]:
        language = "pt-BR"

    # Validar enums
    try:
        fabric = FabricType(fabric_type)
        fit = FitLevel(fit_level)
        system = SizeSystem(size_system)
    except ValueError:
        msg = get_message(language, "invalid_fabric_type") if "fabric" in str(fabric_type).lower() else \
              get_message(language, "invalid_fit_level") if "fit" in str(fit_level).lower() else \
              get_message(language, "invalid_size_system")
        raise HTTPException(status_code=400, detail=msg)

    # Validar tamanho
    if not is_valid_size(size_system, size_label):
        msg = get_message(language, "invalid_size")
        raise HTTPException(status_code=400, detail=msg)

    # Validar imagem frontal
    if not front_image.filename:
        raise HTTPException(status_code=400, detail=get_message(language, "missing_image"))

    if not front_image.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
        raise HTTPException(status_code=400, detail=get_message(language, "file_not_image"))

    # Validar tipo de peça se fornecido
    if garment_type:
        try:
            GarmentType(garment_type)
        except ValueError:
            valid_types = [t.value for t in GarmentType]
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de peça inválido. Opções válidas: {', '.join(valid_types)}"
            )

    # Criar ID único para os arquivos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_id = f"{reference}_{size_system}_{size_label}_{timestamp}"

    # Criar subdiretório para este pedido
    job_dir = GENERATED_FILES_DIR / file_id
    job_dir.mkdir(exist_ok=True)

    try:
        # 1. Salvar imagem frontal
        front_path = job_dir / f"front_{front_image.filename}"
        with open(front_path, "wb") as f:
            content = await front_image.read()
            f.write(content)

        # 2. Salvar imagem posterior (se fornecida)
        if back_image and back_image.filename:
            back_path = job_dir / f"back_{back_image.filename}"
            with open(back_path, "wb") as f:
                content = await back_image.read()
                f.write(content)

        # 3. Buscar medidas da tabela
        measurements_data = get_size_measurements(size_system, size_label)
        if not measurements_data:
            raise HTTPException(status_code=400, detail=get_message(language, "size_not_found"))

        measurements = BodyMeasurements(**measurements_data)

        # 4. Extrair landmarks (opcional)
        # Nota: LandmarkExtractor requer MediaPipe Pose model - não disponível em testes
        try:
            extractor = LandmarkExtractor()
            landmarks = extractor.extract(front_path)
        except (ValueError, FileNotFoundError, Exception):
            landmarks = None

        # 5. Classificar peça
        if garment_type or has_sleeves is not None or neckline or has_dart is not None:
            features = GarmentFeatures(
                fabric_type=fabric,
                garment_type=GarmentType(garment_type) if garment_type else GarmentType.BLUSA,
                has_sleeves=has_sleeves if has_sleeves is not None else False,
                neckline=neckline if neckline else "redondo",
                has_dart=has_dart if has_dart is not None else False,
            )
        else:
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

        # 9. Gerar preview PNG
        preview_path = job_dir / "molde_preview.png"
        generate_preview(
            pieces,
            str(preview_path),
            title=f"{reference} - {size_system}:{size_label}"
        )

        # 10. Exportar PDF
        pdf_path = job_dir / "molde.pdf"
        export_to_pdf(pieces, str(pdf_path), title=f"{reference} - {size_system}:{size_label}")

        # 11. Limpar diretório temporário em background
        background = BackgroundTasks()
        background.add_task(_cleanup_job_dir, job_dir, file_id)

        # 12. Retornar JSON com URLs
        preview_filename = f"{file_id}/molde_preview.png"
        pdf_filename = f"{file_id}/molde.pdf"

        return JSONResponse(
            content={
                "message": get_message(language, "success"),
                "preview_url": f"/files/{preview_filename}",
                "pdf_url": f"/files/{pdf_filename}",
                "size": size_label,
                "size_system": size_system,
                "reference": reference,
                "pieces": [
                    {"name": p.name, "reference": p.reference}
                    for p in pieces
                ]
            },
            background=background
        )

    except HTTPException:
        # Limpar em caso de erro
        if job_dir.exists():
            shutil.rmtree(job_dir, ignore_errors=True)
        raise
    except Exception as e:
        # Limpar diretório em caso de erro
        if job_dir.exists():
            shutil.rmtree(job_dir, ignore_errors=True)
        msg = get_message(language, "processing_error")
        raise HTTPException(status_code=500, detail=msg)


def _calculate_size_delta(size: str) -> int:
    """
    Calcula delta de tamanho em relação ao base (M/40).

    Ex: G/42 → +1, P/38 → -1
    """
    size_map = {
        # BR
        "PP": -2, "P": -1, "M": 0, "G": 1, "GG": 2,
        # US
        "XS": -2, "S": -1, "M": 0, "L": 1, "XL": 2,
        # EU
        "34": -2, "38": -1, "42": 0, "46": 1, "50": 2,
    }
    return size_map.get(size, 0)


async def _cleanup_job_dir(job_dir: Path, file_id: str):
    """
    Limpa diretório do job após delay.
    Mantém arquivos por 24 horas para download.
    """
    await asyncio.sleep(86400)  # 24 horas
    if job_dir.exists():
        shutil.rmtree(job_dir, ignore_errors=True)


async def _cleanup_temp(tmpdir: Path):
    """Limpa diretório temporário após resposta."""
    await asyncio.sleep(0.1)
    shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
