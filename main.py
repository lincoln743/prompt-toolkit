"""
main.py
=======

Ponto de entrada do Prompt Toolkit.

Fluxo:
    1. Health check do Ollama
    2. Para cada tarefa em tasks.py:
        a. Carrega 5 inputs reais de data/inputs.json
        b. Aplica as 4 tecnicas (ZS, FS, CoT, Role)
        c. Mede tokens, tempo e acuracia
    3. Gera relatorio:
        - tabela CSV
        - graficos PNG
        - recomendacao automatica
    4. Roda teste de temperatura no melhor prompt da primeira tarefa
"""
from __future__ import annotations

import json
from pathlib import Path

from src.evaluator import contar_tokens, medir_acuracia, testar_temperatura
from src.llm_client import LLMClient
from src.report import (
    gerar_tabela,
    grafico_acuracia,
    grafico_custo,
    grafico_temperatura,
    imprimir_resumo,
    recomendar,
)
from src.tasks import listar_tarefas
from src.techniques import TECNICAS

# ====================================================================== #
# Configuracao
# ====================================================================== #
ROOT = Path(__file__).resolve().parent
INPUTS_PATH = ROOT / "data" / "inputs.json"


def carregar_inputs() -> dict:
    with open(INPUTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ====================================================================== #
# Execucao principal
# ====================================================================== #
def main() -> None:
    print("=" * 70)
    print("PROMPT TOOLKIT - Grupo NextGen")
    print("=" * 70)

    # 1. health check
    cliente = LLMClient()
    print(f"[main] modelo: {cliente.model}")
    print(f"[main] host:   {cliente.host}")

    if not cliente.health_check():
        print("\n[ERRO] Ollama nao esta respondendo em " + cliente.host)
        print("       Verifique se rodou 'ollama serve' e 'ollama pull " + cliente.model + "'")
        return

    print("[main] Ollama OK\n")

    # 2. carregar inputs
    inputs_por_tarefa = carregar_inputs()
    tarefas = listar_tarefas()

    resultados: list[dict] = []
    melhor_prompt_para_temp = None  # usado depois no teste de temperatura

    # 3. loop principal: tarefa x tecnica x input
    total_calls = sum(len(inputs_por_tarefa.get(t["nome"], [])) for t in tarefas) * len(TECNICAS)
    call_idx = 0

    for tarefa in tarefas:
        nome = tarefa["nome"]
        inputs = inputs_por_tarefa.get(nome, [])
        if not inputs:
            print(f"[main] AVISO: sem inputs para tarefa '{nome}', pulando")
            continue

        print(f"\n>>> Tarefa: {nome} ({len(inputs)} inputs)")

        for tecnica_nome, tecnica_fn in TECNICAS.items():
            for idx, item in enumerate(inputs):
                call_idx += 1
                input_dados = item["input"]
                esperado = item["esperado"]

                # monta prompt (Role retorna tupla, demais retornam str)
                resultado_tecnica = tecnica_fn(tarefa, input_dados)
                if isinstance(resultado_tecnica, tuple):
                    system, prompt = resultado_tecnica
                else:
                    system, prompt = None, resultado_tecnica

                # envia ao LLM
                try:
                    saida = cliente.chat(prompt, system=system, temperature=0.2)
                except Exception as exc:
                    print(f"  [ERRO {tecnica_nome} #{idx}] {exc}")
                    continue

                acuracia = medir_acuracia(saida["resposta"], esperado)

                # tokens do prompt podem nao vir do servidor; estimar com tiktoken
                tokens_prompt = saida["tokens_prompt"] or contar_tokens(
                    (system or "") + prompt
                )

                resultados.append({
                    "tarefa": nome,
                    "tecnica": tecnica_nome,
                    "input_idx": idx,
                    "acuracia": acuracia,
                    "tokens_prompt": tokens_prompt,
                    "tokens_resposta": saida["tokens_resposta"],
                    "tempo_ms": saida["tempo_ms"],
                    "resposta": saida["resposta"][:200],  # truncado para CSV
                })

                # guarda primeiro prompt para teste de temperatura
                if melhor_prompt_para_temp is None:
                    melhor_prompt_para_temp = (prompt, system, nome, tecnica_nome)

                print(
                    f"  [{call_idx}/{total_calls}] {tecnica_nome:18s} "
                    f"input#{idx} -> ac={acuracia:.2f} "
                    f"tk={saida['tokens_resposta']:3d} "
                    f"t={saida['tempo_ms']:4d}ms"
                )

    # 4. relatorio
    if not resultados:
        print("\n[main] nenhum resultado para reportar")
        return

    df = gerar_tabela(resultados)
    imprimir_resumo(df)
    recomendar(df)

    print("[main] gerando graficos...")
    p1 = grafico_acuracia(df)
    p2 = grafico_custo(df)
    print(f"  - {p1}")
    print(f"  - {p2}")

    # 5. teste de temperatura
    if melhor_prompt_para_temp:
        prompt, system, t_nome, tec_nome = melhor_prompt_para_temp
        print(f"\n[main] teste de temperatura em '{t_nome}' / {tec_nome}...")
        try:
            res_temp = testar_temperatura(
                cliente, prompt, system=system,
                temperaturas=[0.1, 0.5, 1.0], repeticoes=3,
            )
            for r in res_temp:
                print(
                    f"  T={r['temperatura']}: consist={r['consistencia']} "
                    f"tokens={r['tokens_medio']} t={r['tempo_medio_ms']}ms"
                )
            p3 = grafico_temperatura(res_temp)
            if p3:
                print(f"  - {p3}")
        except Exception as exc:
            print(f"[main] teste de temperatura falhou: {exc}")

    print("\n[main] EXECUCAO CONCLUIDA")
    print(f"[main] outputs em: {ROOT / 'output'}")


if __name__ == "__main__":
    main()
