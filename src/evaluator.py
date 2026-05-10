"""
evaluator.py
============

Mede qualidade, custo e consistencia das respostas do LLM.

Funcoes:
    - contar_tokens(texto)        : usa tiktoken (cl100k_base) para
                                    estimar o consumo de tokens.
    - medir_acuracia(resp, esperado): compara resposta com saida
                                      esperada (match exato p/ strings,
                                      match estrutural p/ dicts JSON,
                                      match por keywords p/ textos
                                      longos).
    - medir_consistencia(respostas): % de respostas iguais entre
                                     repeticoes da mesma pergunta.
    - testar_temperatura(...)     : roda o mesmo prompt em
                                    temperaturas diferentes e mede
                                    consistencia.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from typing import Iterable, List, Union

import tiktoken

from src.llm_client import LLMClient

# Encoder reutilizavel - cl100k_base e o encoder do GPT-4 (boa aproximacao)
_ENCODER = tiktoken.get_encoding("cl100k_base")


# ====================================================================== #
# Contagem de tokens
# ====================================================================== #
def contar_tokens(texto: str) -> int:
    """Conta tokens usando tiktoken (cl100k_base)."""
    if not texto:
        return 0
    return len(_ENCODER.encode(texto))


# ====================================================================== #
# Medicao de acuracia
# ====================================================================== #
def _normalizar(texto: str) -> str:
    """Lowercase + remove pontuacao + colapsa espacos."""
    texto = texto.lower().strip()
    texto = re.sub(r"[^\w\sáéíóúâêôãõç]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def _extrair_json(texto: str) -> Union[dict, None]:
    """Tenta extrair o primeiro JSON encontrado em uma string."""
    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def medir_acuracia(resposta: str, esperado: Union[str, dict, list]) -> float:
    """
    Mede acuracia da resposta em relacao ao output esperado.

    - Se `esperado` e str:  match exato (normalizado) -> 1.0 ou 0.0
                            ou match por keywords (>= 60% de overlap) -> 1.0
    - Se `esperado` e dict: comparacao campo a campo, retorna a fracao
                            de campos corretos.
    - Se `esperado` e list: % de keywords presentes na resposta.
    """
    if resposta is None:
        return 0.0

    # ---- caso DICT: extracao estruturada -----
    if isinstance(esperado, dict):
        extraido = _extrair_json(resposta)
        if extraido is None:
            return 0.0
        acertos = 0
        total = len(esperado)
        for chave, valor in esperado.items():
            valor_extraido = extraido.get(chave)
            if valor_extraido is None:
                continue
            if _normalizar(str(valor)) == _normalizar(str(valor_extraido)):
                acertos += 1
        return acertos / total if total else 0.0

    # ---- caso LIST: keywords -----
    if isinstance(esperado, list):
        resp_norm = _normalizar(resposta)
        if not esperado:
            return 1.0
        encontrados = sum(1 for kw in esperado if _normalizar(kw) in resp_norm)
        return encontrados / len(esperado)

    # ---- caso STR -----
    resp_norm = _normalizar(resposta)
    esperado_norm = _normalizar(str(esperado))

    # match exato (palavra contida)
    if esperado_norm in resp_norm or resp_norm == esperado_norm:
        return 1.0

    # match por overlap de palavras
    palavras_resp = set(resp_norm.split())
    palavras_esp = set(esperado_norm.split())
    if not palavras_esp:
        return 0.0
    overlap = len(palavras_resp & palavras_esp) / len(palavras_esp)
    return 1.0 if overlap >= 0.6 else 0.0


# ====================================================================== #
# Medicao de consistencia
# ====================================================================== #
def medir_consistencia(respostas: Iterable[str]) -> float:
    """
    Mede a fracao da resposta mais comum em N execucoes.

    Ex: 5 respostas, 4 iguais -> consistencia = 0.8.
    """
    respostas = [_normalizar(r) for r in respostas if r]
    if not respostas:
        return 0.0
    contagem = Counter(respostas)
    mais_comum = contagem.most_common(1)[0][1]
    return mais_comum / len(respostas)


# ====================================================================== #
# Teste de temperatura
# ====================================================================== #
def testar_temperatura(
    cliente: LLMClient,
    prompt: str,
    system: str = None,
    temperaturas: List[float] = (0.1, 0.5, 1.0),
    repeticoes: int = 3,
) -> List[dict]:
    """
    Executa o mesmo prompt em multiplas temperaturas e mede consistencia.

    Returns:
        Lista de dicts, um por temperatura, com:
            - temperatura
            - consistencia
            - tokens_medio
            - tempo_medio_ms
            - amostras (lista das respostas obtidas)
    """
    resultados = []
    for temp in temperaturas:
        respostas, tokens, tempos = [], [], []
        for _ in range(repeticoes):
            r = cliente.chat(prompt, system=system, temperature=temp)
            respostas.append(r["resposta"])
            tokens.append(r["tokens_resposta"])
            tempos.append(r["tempo_ms"])
        resultados.append({
            "temperatura": temp,
            "consistencia": round(medir_consistencia(respostas), 3),
            "tokens_medio": round(sum(tokens) / len(tokens), 1),
            "tempo_medio_ms": round(sum(tempos) / len(tempos), 1),
            "amostras": respostas,
        })
    return resultados
