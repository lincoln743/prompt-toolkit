"""
prompt_builder.py
=================

Modulo responsavel por montar prompts pela anatomia (Aula 05):

    PROMPT = INSTRUCAO + CONTEXTO + INPUT_DADOS + FORMATO_OUTPUT

Aplica o principio fundamental de SEPARAR INSTRUCAO DE DADOS, usando
delimitadores claros (### secoes) que reduzem a chance do modelo
"misturar" contexto com input.
"""
from __future__ import annotations

from typing import Iterable, Optional


class PromptBuilderError(ValueError):
    """Erro de validacao na montagem do prompt."""


def montar_prompt(
    instrucao: str,
    contexto: Optional[str] = None,
    input_dados: str = "",
    formato_output: Optional[str] = None,
) -> str:
    """
    Monta um prompt seguindo a anatomia da Aula 05.

    Args:
        instrucao:      o que o modelo deve fazer (verbo de acao).
        contexto:       informacoes de apoio (opcional).
        input_dados:    o dado concreto a ser processado.
        formato_output: como a resposta deve ser estruturada.

    Returns:
        String final do prompt, com delimitadores explicitos.

    Raises:
        PromptBuilderError: se instrucao ou input_dados estiverem vazios.
    """
    if not instrucao or not instrucao.strip():
        raise PromptBuilderError("instrucao nao pode ser vazia")
    if not input_dados or not input_dados.strip():
        raise PromptBuilderError("input_dados nao pode ser vazio")

    blocos = [f"### INSTRUCAO\n{instrucao.strip()}"]

    if contexto and contexto.strip():
        blocos.append(f"### CONTEXTO\n{contexto.strip()}")

    blocos.append(f"### INPUT\n{input_dados.strip()}")

    if formato_output and formato_output.strip():
        blocos.append(f"### FORMATO DE SAIDA\n{formato_output.strip()}")

    blocos.append("### RESPOSTA")
    return "\n\n".join(blocos)


def adicionar_exemplos(prompt: str, exemplos: Iterable[dict]) -> str:
    """
    Insere exemplos few-shot no prompt (Aula 06).

    Cada exemplo e um dict com chaves 'input' e 'output'. Os exemplos sao
    inseridos imediatamente antes do bloco ### INPUT, no formato:

        ### EXEMPLOS
        Input: "..."
        Output: "..."

    Args:
        prompt:   prompt base montado por `montar_prompt`.
        exemplos: lista de dicts {'input': str, 'output': str}.

    Returns:
        Prompt enriquecido com exemplos.
    """
    exemplos = list(exemplos)
    if not exemplos:
        return prompt

    bloco_exemplos = ["### EXEMPLOS"]
    for ex in exemplos:
        if "input" not in ex or "output" not in ex:
            raise PromptBuilderError("cada exemplo precisa ter 'input' e 'output'")
        out = ex["output"]
        # serializa dict como JSON-like string para legibilidade
        if isinstance(out, dict):
            import json
            out = json.dumps(out, ensure_ascii=False)
        bloco_exemplos.append(f'Input: "{ex["input"]}"\nOutput: {out}')

    bloco_str = "\n\n".join(bloco_exemplos)

    # injeta antes do ### INPUT
    if "### INPUT" in prompt:
        return prompt.replace("### INPUT", f"{bloco_str}\n\n### INPUT", 1)
    return f"{bloco_str}\n\n{prompt}"


def adicionar_cot(prompt: str, passos: Iterable[str]) -> str:
    """
    Adiciona instrucao de chain-of-thought (raciocinio passo a passo).

    Args:
        prompt: prompt base.
        passos: lista de instrucoes de raciocinio na ordem desejada.

    Returns:
        Prompt com bloco ### RACIOCINIO inserido antes do ### RESPOSTA.
    """
    passos = list(passos)
    if not passos:
        return prompt

    linhas = ["### RACIOCINIO PASSO A PASSO"]
    linhas.append("Antes de responder, pense em voz alta seguindo estes passos:")
    for i, passo in enumerate(passos, 1):
        linhas.append(f"{i}. {passo}")
    linhas.append("Em seguida, escreva a resposta final no formato pedido.")

    bloco = "\n".join(linhas)

    if "### RESPOSTA" in prompt:
        return prompt.replace("### RESPOSTA", f"{bloco}\n\n### RESPOSTA", 1)
    return f"{prompt}\n\n{bloco}"
