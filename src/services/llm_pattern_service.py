"""
Serviço de geração de moldes via LLM (Modelista Virtual).
Integra com o prompt de sistema fornecido para gerar JSON técnico.
"""
import json
import logging
from typing import List, Optional
import httpx
from src.models.pattern_piece import PatternPiece, Point2D
from src.vision.garment_classifier import GarmentFeatures

logger = logging.getLogger(__name__)

class LLMPatternService:
    """
    Serviço que traduz pedidos de usuário em moldes industriais via LLM.
    Suporta Ollama (local) e APIs Cloud.
    """
    
    def __init__(self, api_base: str = "http://localhost:11434/api/chat", model: str = "llama3"):
        self.api_base = api_base
        self.model = model
        self.system_prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        try:
            with open("src/services/prompts/modelista_virtual.txt", "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Erro ao carregar prompt: {e}")
            return "Você é um modelista industrial sênior. Retorne apenas JSON."

    async def generate_draft(self, features: GarmentFeatures, system_size: str, size_val: str, idioma: str = "pt-BR") -> Optional[dict]:
        """
        Envia os parâmetros para o LLM e recupera o JSON do molde.
        """
        user_input = {
            "sistema": system_size,
            "tamanho": size_val,
            "tipo_peca": features.garment_type.value,
            "tecido": features.fabric_type.value,
            "caimento": features.caimento if hasattr(features, 'caimento') else "padrao",
            "possui_manga": features.has_sleeves,
            "possui_gola": features.has_collar,
            "possui_pence": features.has_dart,
            "decote": features.neckline,
            "idioma_saida": idioma,
            "molde_id": f"AI-{size_val}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": json.dumps(user_input)}
            ],
            "stream": False,
            "options": {
                "temperature": 0.2
            }
        }

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(self.api_base, json=payload)
                if response.status_code == 200:
                    result = response.json()
                    message_content = result.get("message", {}).get("content", "{}")
                    # Tentar limpar se a IA retornar markdown
                    if "```json" in message_content:
                        message_content = message_content.split("```json")[1].split("```")[0].strip()
                    elif "```" in message_content:
                        message_content = message_content.split("```")[1].split("```")[0].strip()
                    return json.loads(message_content)
                else:
                    logger.error(f"Erro API LLM: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Erro ao conectar com Ollama: {e}")
            return None

    def parse_llm_response(self, data: dict) -> List[PatternPiece]:
        """
        Converte o JSON retornado pela IA em objetos PatternPiece.
        """
        pieces = []
        if "pecas" not in data:
            return []

        for p_data in data["pecas"]:
            # Pontos do contorno ordenado
            points_map = p_data.get("pontos", {})
            outline_seq = p_data.get("contorno_ordenado", [])
            
            outline = []
            for key in outline_seq:
                if key in points_map:
                    pt = points_map[key]
                    outline.append((float(pt[0]), float(pt[1])))
            
            # Curvas
            curves = p_data.get("curvas", [])
            
            # Dimensões (cotas)
            llm_dims = p_data.get("dimensoes_detalhadas", []) # O prompt usa dimensoes mas vamos flexibilizar
            
            # Traduzir para o nosso modelo
            piece = PatternPiece(
                name=p_data.get("nome", "Peça Generativa"),
                size=data.get("ficha_tecnica", {}).get("tamanho", "M"),
                reference=p_data.get("codigo", "AI-REF"),
                cut_quantity=2 if "espelhado" in p_data.get("instrucao_corte", "") else 1,
                outline=outline,
                curves=curves,
                instructions=p_data.get("instrucao_corte", ""),
                assembly_steps=data.get("instrucoes_montagem", {}).get("pt_BR", [])
            )
            pieces.append(piece)
            
        return pieces
