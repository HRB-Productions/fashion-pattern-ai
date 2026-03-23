"""
Mensagens localizadas para a API Fashion Pattern AI.
"""

MESSAGES = {
    "pt-BR": {
        "invalid_size": "Tamanho inválido para o sistema selecionado",
        "missing_image": "Imagem frontal é obrigatória",
        "missing_image_back": "Imagem posterior é obrigatória para este tipo de peça",
        "processing_error": "Erro ao processar o molde",
        "success": "Molde gerado com sucesso",
        "invalid_fabric_type": "Tipo de tecido inválido",
        "invalid_fit_level": "Nível de caimento inválido",
        "invalid_size_system": "Sistema de tamanhos inválido",
        "file_not_image": "O arquivo enviado não é uma imagem válida",
        "size_not_found": "Tamanho não encontrado na tabela",
    },
    "en-US": {
        "invalid_size": "Invalid size for selected system",
        "missing_image": "Front image is required",
        "missing_image_back": "Back image is required for this garment type",
        "processing_error": "Error processing pattern",
        "success": "Pattern generated successfully",
        "invalid_fabric_type": "Invalid fabric type",
        "invalid_fit_level": "Invalid fit level",
        "invalid_size_system": "Invalid size system",
        "file_not_image": "Uploaded file is not a valid image",
        "size_not_found": "Size not found in table",
    },
    "es-ES": {
        "invalid_size": "Talla inválida para el sistema seleccionado",
        "missing_image": "Imagen frontal es obligatoria",
        "missing_image_back": "Imagen posterior es obligatoria para este tipo de prenda",
        "processing_error": "Error al procesar el molde",
        "success": "Molde generado con éxito",
        "invalid_fabric_type": "Tipo de tela inválido",
        "invalid_fit_level": "Nivel de ajuste inválido",
        "invalid_size_system": "Sistema de tallas inválido",
        "file_not_image": "El archivo subido no es una imagen válida",
        "size_not_found": "Talla no encontrada en la tabla",
    },
}


def get_message(language: str, key: str) -> str:
    """
    Retorna mensagem localizada para o idioma e chave especificados.

    Args:
        language: Código do idioma (ex: "pt-BR", "en-US", "es-ES")
        key: Chave da mensagem

    Returns:
        Mensagem localizada ou fallback para inglês
    """
    if language not in MESSAGES:
        language = "en-US"

    messages = MESSAGES.get(language, MESSAGES["en-US"])
    return messages.get(key, MESSAGES["en-US"].get(key, key))
