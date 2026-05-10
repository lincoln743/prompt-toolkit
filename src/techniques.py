"""
techniques.py
=============

Implementa as 4 tecnicas de prompting estudadas:

    - Zero-Shot      (Aula 06)
    - Few-Shot       (Aula 06)
    - Chain-of-Thought (Aula 06)
    - Role Prompting (Aula 07)

Cada funcao recebe a tarefa (dict definido em tasks.py) e o input cru,
e retorna o prompt pronto para envio ao LLM. Para Role Prompting, retorna
uma TUPLA (system, user) ja que o system prompt e separado.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

from src.prompt_builder import (
    adicionar_cot,
    adicionar_exemplos,
    montar_prompt,
)

# Caminho para o arquivo de personas (carregado uma vez)
_PERSONAS_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system_prompts.json"


def _load_personas() -> dict:
    if not _PERSONAS_PATH.exists():
        return {}
    with open(_PERSONAS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ====================================================================== #
# 1. ZERO-SHOT
# ====================================================================== #
def zero_shot(tarefa: dict, input_dados: str) -> str:
    """
    Prompt direto, sem exemplos. Apenas instrucao + formato de saida.
    """
    return montar_prompt(
        instrucao=tarefa["instrucao"],
        input_dados=input_dados,
        formato_output=tarefa.get("formato_output"),
    )


# ====================================================================== #
# 2. FEW-SHOT
# ====================================================================== #
def few_shot(tarefa: dict, input_dados: str) -> str:
    """
    Prompt com 2-3 exemplos do proprio tarefa['exemplos_fewshot'].
    """
    base = montar_prompt(
        instrucao=tarefa["instrucao"],
        input_dados=input_dados,
        formato_output=tarefa.get("formato_output"),
    )
    exemplos = tarefa.get("exemplos_fewshot", [])
    return adicionar_exemplos(base, exemplos)


# ====================================================================== #
# 3. CHAIN-OF-THOUGHT
# ====================================================================== #
def chain_of_thought(tarefa: dict, input_dados: str) -> str:
    """
    Prompt com raciocinio explicito passo a passo.
    """
    base = montar_prompt(
        instrucao=tarefa["instrucao"],
        input_dados=input_dados,
        formato_output=tarefa.get("formato_output"),
    )
    passos = tarefa.get("passos_cot", [])
    return adicionar_cot(base, passos)


# ====================================================================== #
# 4. ROLE PROMPTING
# ====================================================================== #
def role_prompting(tarefa: dict, input_dados: str) -> Tuple[str, str]:
    """
    Define um system prompt detalhado (persona) e usa user prompt enxuto.

    Returns:
        Tupla (system, user). O LLMClient envia `system` separado.
    """
    personas = _load_personas()
    chave = tarefa.get("persona")
    persona = personas.get(chave)

    if not persona:
        # fallback: persona generica de analista
        persona = (
            "Voce e um analista senior, objetivo e tecnico. "
            "Siga estritamente as instrucoes do usuario e o formato pedido."
        )

    user_prompt = montar_prompt(
        instrucao=tarefa["instrucao"],
        input_dados=input_dados,
        formato_output=tarefa.get("formato_output"),
    )
    return persona, user_prompt


# ====================================================================== #
# Registro central das tecnicas - usado pelo main.py
# ====================================================================== #
TECNICAS = {
    "zero_shot": zero_shot,
    "few_shot": few_shot,
    "chain_of_thought": chain_of_thought,
    "role_prompting": role_prompting,
}
