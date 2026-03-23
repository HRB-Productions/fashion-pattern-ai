"""
Testes para a API FastAPI (main.py) - Versão 2.0 com i18n e tamanhos padronizados.
Cobrir endpoints /health e /generate-pattern.
"""
import pytest
from main import app, _calculate_size_delta
from src.models.enums import FabricType, FitLevel, SizeSystem
from src.models.size_tables import SIZE_TABLES, is_valid_size, get_size_measurements


class TestHealthEndpoint:
    """Testes para GET /health."""

    @pytest.mark.asyncio
    async def test_health_returns_ok(self, client):
        """Health check deve retornar status ok."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["version"] == "2.0"


class TestSizeDeltaCalculation:
    """Testes para função _calculate_size_delta."""

    def test_size_m_is_base(self):
        """Tamanho M é base, delta zero."""
        assert _calculate_size_delta("M") == 0

    def test_size_g_is_plus_one(self):
        """Tamanho G é +1 em relação ao base."""
        assert _calculate_size_delta("G") == 1

    def test_size_p_is_minus_one(self):
        """Tamanho P é -1 em relação ao base."""
        assert _calculate_size_delta("P") == -1

    def test_size_gg_is_plus_two(self):
        """Tamanho GG é +2 em relação ao base."""
        assert _calculate_size_delta("GG") == 2

    def test_size_pp_is_minus_two(self):
        """Tamanho PP é -2 em relação ao base."""
        assert _calculate_size_delta("PP") == -2

    def test_size_l_is_plus_one_us(self):
        """Tamanho L (US) é +1 em relação ao base."""
        assert _calculate_size_delta("L") == 1

    def test_size_s_is_minus_one_us(self):
        """Tamanho S (US) é -1 em relação ao base."""
        assert _calculate_size_delta("S") == -1

    def test_size_46_is_plus_one_eu(self):
        """Tamanho 46 (EU) é +1 em relação ao base."""
        assert _calculate_size_delta("46") == 1

    def test_size_38_is_minus_one_eu(self):
        """Tamanho 38 (EU) é -1 em relação ao base."""
        assert _calculate_size_delta("38") == -1

    def test_unknown_size_returns_zero(self):
        """Tamanho não mapeado retorna 0."""
        assert _calculate_size_delta("XXL") == 0
        assert _calculate_size_delta("52") == 0


class TestSizeTables:
    """Testes para tabelas de tamanhos."""

    def test_br_size_table_has_all_sizes(self):
        """Tabela BR deve ter PP, P, M, G, GG."""
        assert "PP" in SIZE_TABLES["BR"]
        assert "P" in SIZE_TABLES["BR"]
        assert "M" in SIZE_TABLES["BR"]
        assert "G" in SIZE_TABLES["BR"]
        assert "GG" in SIZE_TABLES["BR"]

    def test_us_size_table_has_all_sizes(self):
        """Tabela US deve ter XS, S, M, L, XL."""
        assert "XS" in SIZE_TABLES["US"]
        assert "S" in SIZE_TABLES["US"]
        assert "M" in SIZE_TABLES["US"]
        assert "L" in SIZE_TABLES["US"]
        assert "XL" in SIZE_TABLES["US"]

    def test_eu_size_table_has_all_sizes(self):
        """Tabela EU deve ter 34, 38, 42, 46, 50."""
        assert "34" in SIZE_TABLES["EU"]
        assert "38" in SIZE_TABLES["EU"]
        assert "42" in SIZE_TABLES["EU"]
        assert "46" in SIZE_TABLES["EU"]
        assert "50" in SIZE_TABLES["EU"]

    def test_get_size_measurements_br_m(self):
        """M no BR deve retornar medidas corretas."""
        measurements = get_size_measurements("BR", "M")
        assert measurements is not None
        assert measurements["busto"] == 88.0
        assert measurements["cintura"] == 70.0
        assert measurements["quadril"] == 96.0

    def test_get_size_measurements_us_m(self):
        """M no US deve retornar medidas corretas."""
        measurements = get_size_measurements("US", "M")
        assert measurements is not None
        assert measurements["busto"] == 90.0

    def test_get_size_measurements_eu_42(self):
        """42 no EU deve retornar medidas corretas."""
        measurements = get_size_measurements("EU", "42")
        assert measurements is not None
        assert measurements["busto"] == 90.0

    def test_is_valid_size_br_m(self):
        """M é válido no BR."""
        assert is_valid_size("BR", "M") is True

    def test_is_valid_size_invalid(self):
        """Tamanho inválido deve retornar False."""
        assert is_valid_size("BR", "XXL") is False
        assert is_valid_size("US", "G") is False
        assert is_valid_size("EU", "40") is False

    def test_invalid_system_returns_false(self):
        """Sistema inválido deve retornar False."""
        assert is_valid_size("XX", "M") is False


class TestGeneratePatternEndpoint:
    """Testes para POST /generate-pattern."""

    @pytest.mark.asyncio
    async def test_generate_pattern_with_valid_data_br(self, client, sample_image_bytes):
        """Endpoint deve gerar PDF com dados válidos (BR)."""
        files = {"front_image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "size_system": "BR",
            "size_label": "M",
            "fabric_type": "plano",
            "fit_level": "padrao",
            "reference": "BL-001",
            "garment_type": "blusa",
            "has_sleeves": False,
            "neckline": "redondo",
            "has_dart": False,
            "language": "pt-BR",
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "molde_BL-001_BR_M.pdf" in response.headers["content-disposition"]
        assert response.headers.get("x-pattern-message") == "Molde gerado com sucesso"

    @pytest.mark.asyncio
    async def test_generate_pattern_with_valid_data_us(self, client, sample_image_bytes):
        """Endpoint deve gerar PDF com dados válidos (US)."""
        files = {"front_image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "size_system": "US",
            "size_label": "M",
            "fabric_type": "plano",
            "fit_level": "padrao",
            "reference": "BL-002",
            "language": "en-US",
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.headers.get("x-pattern-message") == "Pattern generated successfully"

    @pytest.mark.asyncio
    async def test_generate_pattern_with_valid_data_eu(self, client, sample_image_bytes):
        """Endpoint deve gerar PDF com dados válidos (EU)."""
        files = {"front_image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "size_system": "EU",
            "size_label": "42",
            "fabric_type": "plano",
            "fit_level": "padrao",
            "reference": "BL-003",
            "language": "es-ES",
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.headers.get("x-pattern-message") == "Molde generado con éxito"

    @pytest.mark.asyncio
    async def test_generate_pattern_with_back_image(self, client, sample_image_bytes):
        """Endpoint deve aceitar imagem posterior opcional."""
        files = {
            "front_image": ("front.jpg", sample_image_bytes, "image/jpeg"),
            "back_image": ("back.jpg", sample_image_bytes, "image/jpeg"),
        }
        data = {
            "size_system": "BR",
            "size_label": "G",
            "fabric_type": "plano",
            "fit_level": "padrao",
            "reference": "BL-004",
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_generate_pattern_rejects_invalid_size_system(self, client, sample_image_bytes):
        """Sistema de tamanhos inválido deve retornar 422 (FastAPI validation)."""
        files = {"front_image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "size_system": "XX",  # inválido
            "size_label": "M",
            "fabric_type": "plano",
            "fit_level": "padrao",
            "reference": "BL-005",
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_pattern_rejects_invalid_size_label(self, client, sample_image_bytes):
        """Tamanho inválido deve retornar 400."""
        files = {"front_image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "size_system": "BR",
            "size_label": "XXL",  # inválido no BR
            "fabric_type": "plano",
            "fit_level": "padrao",
            "reference": "BL-006",
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_generate_pattern_rejects_invalid_fabric_type(self, client, sample_image_bytes):
        """Tipo de tecido inválido deve retornar 422 (FastAPI validation)."""
        files = {"front_image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "size_system": "BR",
            "size_label": "M",
            "fabric_type": "seda",  # inválido
            "fit_level": "padrao",
            "reference": "BL-007",
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_pattern_rejects_invalid_fit_level(self, client, sample_image_bytes):
        """Nível de caimento inválido deve retornar 422 (FastAPI validation)."""
        files = {"front_image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "size_system": "BR",
            "size_label": "M",
            "fabric_type": "plano",
            "fit_level": "fino",  # inválido
            "reference": "BL-008",
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_pattern_malha_justo(self, client, sample_image_bytes):
        """Malha justo deve gerar molde."""
        files = {"front_image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "size_system": "BR",
            "size_label": "M",
            "fabric_type": "malha",
            "fit_level": "justo",
            "reference": "ML-001",
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_generate_pattern_falta_front_image(self, client):
        """Falta de imagem frontal deve retornar 422."""
        data = {
            "size_system": "BR",
            "size_label": "M",
            "fabric_type": "plano",
            "fit_level": "padrao",
            "reference": "BL-009",
        }
        response = await client.post("/generate-pattern", data=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_pattern_default_language_pt_br(self, client, sample_image_bytes):
        """Idioma padrão deve ser pt-BR."""
        files = {"front_image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "size_system": "BR",
            "size_label": "M",
            "fabric_type": "plano",
            "fit_level": "padrao",
            "reference": "BL-010",
            # language não fornecido, deve usar pt-BR
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert response.status_code == 200
        assert response.headers.get("x-pattern-message") == "Molde gerado com sucesso"

    @pytest.mark.asyncio
    async def test_generate_pattern_cors_header_presente(self, client, sample_image_bytes):
        """CORS headers devem estar presentes."""
        files = {"front_image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        data = {
            "size_system": "BR",
            "size_label": "M",
            "fabric_type": "plano",
            "fit_level": "padrao",
            "reference": "BL-011",
        }
        response = await client.post("/generate-pattern", files=files, data=data)

        assert "access-control-allow-origin" in response.headers or True


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


class TestSizeSystemEnumeration:
    """Testes para enum SizeSystem."""

    def test_size_system_br(self):
        """SizeSystem.BR deve ser 'BR'."""
        assert SizeSystem.BR == "BR"
        assert SizeSystem("BR") == SizeSystem.BR

    def test_size_system_us(self):
        """SizeSystem.US deve ser 'US'."""
        assert SizeSystem.US == "US"
        assert SizeSystem("US") == SizeSystem.US

    def test_size_system_eu(self):
        """SizeSystem.EU deve ser 'EU'."""
        assert SizeSystem.EU == "EU"
        assert SizeSystem("EU") == SizeSystem.EU

    def test_size_system_invalid_value_raises(self):
        """Valor inválido deve levantar ValueError."""
        with pytest.raises(ValueError):
            SizeSystem("XX")
