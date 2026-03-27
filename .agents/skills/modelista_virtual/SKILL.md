---
name: Modelista Virtual
description: Sistema especialista em modelagem industrial de roupas para geração de moldes técnicos via JSON.
---

# Skill: Modelista Virtual

Este skill define as regras de negócio e o prompt de sistema para a geração de moldes industriais de alta fidelidade.

## Tabelas de Medidas Industriais

### SISTEMA BRASIL — ABNT NBR 16933
| Tamanho | Busto | Cintura | Quadril | Alt.Busto | Alt.Cava | Larg.Costas | Comp.Costas |
|---------|-------|---------|---------|-----------|----------|-------------|-------------|
| PP      | 80    | 62      | 88      | 24        | 18.5     | 16.5        | 38          |
| P       | 84    | 66      | 92      | 24.5      | 19       | 17          | 39          |
| M       | 88    | 70      | 96      | 25        | 19.5     | 17.5        | 40          |
| G       | 96    | 78      | 104     | 26        | 20.5     | 18.5        | 41.5        |
| GG      | 104   | 86      | 112     | 27        | 21.5     | 19.5        | 43          |

### SISTEMA EUA — ASTM D5585
| Size | Bust  | Waist | Hip   | Back Length | Armhole Depth |
|------|-------|-------|-------|-------------|---------------|
| XS   | 80    | 62    | 88    | 39          | 19            |
| S    | 84    | 66    | 92    | 40          | 19.5          |
| M    | 88-92 | 70-74 | 96-100| 41          | 20.5          |
| L    | 96-100| 78-82 | 104-108| 42.5       | 21.5          |
| XL   | 104   | 86    | 112   | 43.5        | 22            |

## Fórmulas de Trazado (Destaques)

- **Cava Frente**: Curva spline passando por M → N → J (Alt_cava/2).
- **Decote Redondo**: Raio = Busto/20 + 1.5.
- **Folgas (Ease)**: +4cm para caimento padrão em tecido plano; +1cm em malha.
- **Margens de Costura**: 1.5cm laterais/ombros; 1.0cm decote/cava; 3cm barra (malha).

## Regras de Geração JSON

A IA deve retornar peças com IDs `FRENTE`, `COSTAS`, `MANGA`, etc. Cada peça deve conter:
- `pontos`: Dicionário de coordenadas X, Y.
- `curvas`: Lista de objetos Bezier (pontos de controle).
- `contorno_ordenado`: Lista de chaves de pontos na ordem correta para desenho.

## Implementação Técnica
Localizada em `src/services/llm_pattern_service.py`. Consome o arquivo de prompt em `src/services/prompts/modelista_virtual.txt`.
