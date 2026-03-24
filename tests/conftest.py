"""
Configurações globais para os testes.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from main import app
from unittest.mock import patch, MagicMock


# Configurar pytest-asyncio
def pytest_configure(config):
    config.option.asyncio_mode = "auto"
    config.addinivalue_line(
        "markers", "asyncio: mark test as an asyncio test."
    )


@pytest.fixture(scope="function", autouse=True)
def mock_vision_components():
    """Mock para componentes de visão que causam bloqueio nos testes."""
    # Mock LandmarkExtractor no main.py (já importado)
    with patch('main.LandmarkExtractor') as mock_landmark:
        mock_instance = MagicMock()
        mock_instance.extract.side_effect = ValueError("Pose não detectada")
        mock_landmark.return_value = mock_instance

        yield mock_landmark


@pytest.fixture
async def client():
    """Cliente HTTP assíncrono para testes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(base_url="http://test", transport=transport) as ac:
        yield ac


@pytest.fixture
def sample_image_bytes():
    """Bytes de imagem JPEG dummy para upload."""
    # JPEG minimal válido (1x1 pixel)
    return (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
        b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
        b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9telecom'
        b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x01'
        b'\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
        b'\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01'
        b'\x02\x03\x00\x04\x11\x05\x1221A\x14aQ\x1eq\x89\x1aB\x12b\x12\x8a\xea\x3c\x9c\x3d\x9d'
        b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd5\x00\x00\x00\xff\xd9'
    )
