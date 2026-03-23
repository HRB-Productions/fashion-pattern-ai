"""
Testes para a API FastAPI (main.py).
Cobrir endpoints /health e /generate-pattern.
"""
import pytest
from main import app, _calculate_size_delta
from src.models.enums import FabricType, FitLevel


class TestHealthEndpoint:
    """Testes para GET /health."""

    @pytest.mark.asyncio
    async def test_health_returns_ok(self, client):
        """Health check deve retornar status ok."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["version"] == "1.0"


class TestSizeDeltaCalculation:
    """Testes para função _calculate_size_delta."""

    def test_size_40_is_base(self):
        """Tamanho 40 é base, delta zero."""
        assert _calculate_size_delta("40") == 0

    def test_size_42_is_plus_one(self):
        """Tamanho 42 é +1 em relação ao base."""
        assert _calculate_size_delta("42") == 1

    def test_size_38_is_minus_one(self):
        """Tamanho 38 é -1 em relação ao base."""
        assert _calculate_size_delta("38") == -1

    def test_size_44_is_plus_two(self):
        """Tamanho 44 é +2 em relação ao base."""
        assert _calculate_size_delta("44") == 2

    def test_size_36_is_minus_two(self):
        """Tamanho 36 é -2 em relação ao base."""
        assert _calculate_size_delta("36") == -2

    def test_size_46_is_plus_three(self):
        """Tamanho 46 é +3 em relação ao base."""
        assert _calculate_size_delta("46") == 3

    def test_size_48_is_plus_four(self):
        """Tamanho 48 é +4 em relação ao base."""
        assert _calculate_size_delta("48") == 4

    def test_unknown_size_returns_zero(self):
        """Tamanho não mapeado retorna 0."""
        assert _calculate_size_delta("M") == 0
        assert _calculate_size_delta("G") == 0
        assert _calculate_size_delta("50") == 0


class TestGeneratePatternEndpoint:
    """Testes para POST /generate-pattern."""

    @pytest.mark.asyncio
    async def test_generate_pattern_with_valid_data(self, client, sample_image_bytes):
        """Endpoint deve gerar PDF com dados válidos."""
        import json
        override = {
            "fabric_type": "plano",
            "garment_type": "blusa",
            "has_sleeves": False,
            "neckline": "redondo",
            "has_dart": False,
        }
        files = {"image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "busto": 88.0,
            "cintura": 70.0,
            "quadril": 95.0,
            "altura": 165.0,
            "fabric_type": "plano",
            "fit_level": "padrao",
            "size": "40",
            "reference": "BL-001",
            "override_features": json.dumps(override),
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "molde_BL-001_40.pdf" in response.headers["content-disposition"]

    @pytest.mark.asyncio
    async def test_generate_pattern_rejects_invalid_busto(self, client, sample_image_bytes):
        """Busto fora do range (60-160) deve retornar 400."""
        files = {"image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "busto": 50.0,  # inválido: < 60
            "cintura": 70.0,
            "quadril": 95.0,
            "altura": 165.0,
            "fabric_type": "plano",
            "fit_level": "padrao",
            "size": "40",
            "reference": "BL-001",
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_pattern_rejects_invalid_fabric_type(self, client, sample_image_bytes):
        """Tipo de tecido inválido deve retornar 400."""
        files = {"image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "busto": 88.0,
            "cintura": 70.0,
            "quadril": 95.0,
            "altura": 165.0,
            "fabric_type": "seda",  # inválido
            "fit_level": "padrao",
            "size": "40",
            "reference": "BL-001",
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_pattern_rejects_invalid_fit_level(self, client, sample_image_bytes):
        """Nível de caimento inválido deve retornar 400."""
        files = {"image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "busto": 88.0,
            "cintura": 70.0,
            "quadril": 95.0,
            "altura": 165.0,
            "fabric_type": "plano",
            "fit_level": "fino",  # inválido
            "size": "40",
            "reference": "BL-001",
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_pattern_malha_justo(self, client, sample_image_bytes):
        """Malha justo deve gerar molde com folga negativa."""
        import json
        override = {
            "fabric_type": "malha",
            "garment_type": "blusa",
            "has_sleeves": False,
            "neckline": "redondo",
            "has_dart": False,
        }
        files = {"image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "busto": 88.0,
            "cintura": 70.0,
            "quadril": 95.0,
            "altura": 165.0,
            "fabric_type": "malha",
            "fit_level": "justo",
            "size": "40",
            "reference": "ML-001",
            "override_features": json.dumps(override),
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_generate_pattern_com_manga(self, client, sample_image_bytes):
        """Peça com manga deve gerar molde com 3 peças."""
        import json
        override = {
            "fabric_type": "plano",
            "garment_type": "blusa",
            "has_sleeves": True,
            "neckline": "redondo",
            "has_dart": False,
        }
        files = {"image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "busto": 88.0,
            "cintura": 70.0,
            "quadril": 95.0,
            "altura": 165.0,
            "fabric_type": "plano",
            "fit_level": "padrao",
            "size": "40",
            "reference": "BL-002",
            "override_features": json.dumps(override),
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_generate_pattern_com_override_features(self, client, sample_image_bytes):
        """Override features JSON deve ser aceito."""
        import json
        override = {
            "fabric_type": "plano",
            "garment_type": "blusa",
            "has_sleeves": True,
            "neckline": "redondo",
            "has_dart": False,
        }
        files = {"image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "busto": 88.0,
            "cintura": 70.0,
            "quadril": 95.0,
            "altura": 165.0,
            "fabric_type": "plano",
            "fit_level": "padrao",
            "size": "40",
            "reference": "BL-003",
            "override_features": json.dumps(override),
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_generate_pattern_rejects_invalid_override_features(self, client, sample_image_bytes):
        """Override features JSON inválido deve retornar 400."""
        files = {"image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "busto": 88.0,
            "cintura": 70.0,
            "quadril": 95.0,
            "altura": 165.0,
            "fabric_type": "plano",
            "fit_level": "padrao",
            "size": "40",
            "reference": "BL-004",
            "override_features": "json-invalido",
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_generate_pattern_falta_imagem(self, client):
        """Falta de imagem deve retornar 422."""
        data = {
            "busto": 88.0,
            "cintura": 70.0,
            "quadril": 95.0,
            "altura": 165.0,
            "fabric_type": "plano",
            "fit_level": "padrao",
            "size": "40",
            "reference": "BL-005",
        }
        response = await client.post("/generate-pattern", data=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_pattern_falta_medida_obrigatoria(self, client, sample_image_bytes):
        """Falta de medida obrigatória deve retornar 422."""
        files = {"image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "busto": 88.0,
            # falta cintura
            "quadril": 95.0,
            "altura": 165.0,
            "fabric_type": "plano",
            "fit_level": "padrao",
            "size": "40",
            "reference": "BL-006",
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_pattern_cors_header_presente(self, client, sample_image_bytes):
        """CORS headers devem estar presentes."""
        import json
        override = {
            "fabric_type": "plano",
            "garment_type": "blusa",
            "has_sleeves": False,
            "neckline": "redondo",
            "has_dart": False,
        }
        files = {"image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "busto": 88.0,
            "cintura": 70.0,
            "quadril": 95.0,
            "altura": 165.0,
            "fabric_type": "plano",
            "fit_level": "padrao",
            "size": "40",
            "reference": "BL-007",
            "override_features": json.dumps(override),
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert response.status_code == 200


class TestFabricTypeEnumeration:
    """Testes para enum FabricType."""

    def test_fabric_type_plano(self):
        """FabricType.PLANO deve ser 'plano'."""
        assert FabricType.PLANO == "plano"
        assert FabricType("plano") == FabricType.PLANO

    def test_fabric_type_malha(self):
        """FabricType.MALHA deve ser 'malha'."""
        assert FabricType.MALHA == "malha"
        assert FabricType("malha") == FabricType.MALHA

    def test_fabric_type_invalid_value_raises(self):
        """Valor inválido deve levantar ValueError."""
        with pytest.raises(ValueError):
            FabricType("seda")


class TestFitLevelEnumeration:
    """Testes para enum FitLevel."""

    def test_fit_level_justo(self):
        """FitLevel.JUSTO deve ser 'justo'."""
        assert FitLevel.JUSTO == "justo"
        assert FitLevel("justo") == FitLevel.JUSTO

    def test_fit_level_padrao(self):
        """FitLevel.PADRAO deve ser 'padrao'."""
        assert FitLevel.PADRAO == "padrao"
        assert FitLevel("padrao") == FitLevel.PADRAO

    def test_fit_level_amplo(self):
        """FitLevel.AMPLO deve ser 'amplo'."""
        assert FitLevel.AMPLO == "amplo"
        assert FitLevel("amplo") == FitLevel.AMPLO

    def test_fit_level_invalid_value_raises(self):
        """Valor inválido deve levantar ValueError."""
        with pytest.raises(ValueError):
            FitLevel("fino")
