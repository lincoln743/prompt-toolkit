"""
report.py
=========

Gera relatorio comparativo a partir dos resultados da execucao:

    - tabela CSV (output/resultados.csv)
    - grafico de acuracia por tecnica/tarefa (PNG)
    - grafico de custo (tokens) por tecnica
    - grafico de consistencia por temperatura
    - recomendacao automatica da melhor tecnica por tarefa
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Dict

import matplotlib

matplotlib.use("Agg")  # backend sem display, para servidores
import matplotlib.pyplot as plt
import pandas as pd


# ====================================================================== #
# Caminhos
# ====================================================================== #
_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
_GRAFICOS_DIR = _OUTPUT_DIR / "graficos"
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
_GRAFICOS_DIR.mkdir(parents=True, exist_ok=True)


# ====================================================================== #
# Tabela CSV
# ====================================================================== #
def gerar_tabela(resultados: List[Dict], salvar_csv: bool = True) -> pd.DataFrame:
    """
    Constroi DataFrame e salva em CSV.

    Args:
        resultados: lista de dicts com chaves:
            tarefa, tecnica, input_idx, acuracia, tokens_prompt,
            tokens_resposta, tempo_ms.
    """
    df = pd.DataFrame(resultados)
    if salvar_csv:
        csv_path = _OUTPUT_DIR / "resultados.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8")
        print(f"[report] CSV salvo em: {csv_path}")
    return df


def imprimir_resumo(df: pd.DataFrame) -> None:
    """Imprime no terminal um resumo agrupado por tarefa+tecnica."""
    if df.empty:
        print("[report] sem resultados")
        return

    resumo = df.groupby(["tarefa", "tecnica"]).agg(
        acuracia_media=("acuracia", "mean"),
        tokens_medio=("tokens_resposta", "mean"),
        tempo_medio_ms=("tempo_ms", "mean"),
    ).round(3).reset_index()

    print("\n" + "=" * 70)
    print("RESUMO COMPARATIVO")
    print("=" * 70)
    print(resumo.to_string(index=False))
    print("=" * 70 + "\n")


# ====================================================================== #
# Graficos
# ====================================================================== #
def grafico_acuracia(df: pd.DataFrame, salvar: bool = True) -> Path:
    """Barras agrupadas: acuracia media por tecnica e tarefa."""
    pivot = df.groupby(["tarefa", "tecnica"])["acuracia"].mean().unstack()

    ax = pivot.plot(kind="bar", figsize=(10, 6), edgecolor="black")
    ax.set_title("Acuracia media por tecnica e tarefa", fontsize=13)
    ax.set_xlabel("Tarefa")
    ax.set_ylabel("Acuracia (0.0 a 1.0)")
    ax.set_ylim(0, 1.05)
    ax.legend(title="Tecnica", loc="lower right")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()

    path = _GRAFICOS_DIR / "acuracia.png"
    if salvar:
        plt.savefig(path, dpi=150)
    plt.close()
    return path


def grafico_custo(df: pd.DataFrame, salvar: bool = True) -> Path:
    """Tokens medios de resposta por tecnica."""
    medias = df.groupby("tecnica")["tokens_resposta"].mean().sort_values()

    fig, ax = plt.subplots(figsize=(8, 5))
    medias.plot(kind="barh", ax=ax, color="steelblue", edgecolor="black")
    ax.set_title("Custo medio (tokens de resposta) por tecnica", fontsize=13)
    ax.set_xlabel("Tokens medios")
    ax.set_ylabel("Tecnica")
    for i, v in enumerate(medias.values):
        ax.text(v + 1, i, f"{v:.0f}", va="center")
    plt.tight_layout()

    path = _GRAFICOS_DIR / "custo.png"
    if salvar:
        plt.savefig(path, dpi=150)
    plt.close()
    return path


def grafico_temperatura(resultados_temp: List[Dict], salvar: bool = True) -> Path:
    """Consistencia por temperatura."""
    if not resultados_temp:
        return None

    df = pd.DataFrame(resultados_temp)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df["temperatura"], df["consistencia"], marker="o", linewidth=2, color="darkorange")
    ax.set_title("Consistencia x Temperatura", fontsize=13)
    ax.set_xlabel("Temperatura")
    ax.set_ylabel("Consistencia (0.0 a 1.0)")
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    for x, y in zip(df["temperatura"], df["consistencia"]):
        ax.annotate(f"{y:.2f}", (x, y), textcoords="offset points", xytext=(0, 8), ha="center")
    plt.tight_layout()

    path = _GRAFICOS_DIR / "temperatura.png"
    if salvar:
        plt.savefig(path, dpi=150)
    plt.close()
    return path


# ====================================================================== #
# Recomendacao automatica
# ====================================================================== #
def recomendar(df: pd.DataFrame) -> List[Dict]:
    """
    Para cada tarefa, escolhe a melhor tecnica considerando:
        - acuracia (peso maior)
        - tokens de resposta (peso negativo - mais barato e melhor)

    Retorna lista de dicts com tarefa, tecnica recomendada e justificativa.
    """
    if df.empty:
        return []

    agg = df.groupby(["tarefa", "tecnica"]).agg(
        acuracia=("acuracia", "mean"),
        tokens=("tokens_resposta", "mean"),
        tempo_ms=("tempo_ms", "mean"),
    ).reset_index()

    # score = acuracia - 0.001 * tokens (penaliza levemente custo)
    agg["score"] = agg["acuracia"] - 0.001 * agg["tokens"]

    recomendacoes = []
    for tarefa, grupo in agg.groupby("tarefa"):
        melhor = grupo.sort_values("score", ascending=False).iloc[0]
        justificativa = (
            f"acuracia={melhor['acuracia']:.2f}, "
            f"tokens_medio={melhor['tokens']:.0f}, "
            f"tempo_medio={melhor['tempo_ms']:.0f}ms"
        )
        recomendacoes.append({
            "tarefa": tarefa,
            "tecnica_recomendada": melhor["tecnica"],
            "justificativa": justificativa,
        })

    print("\n" + "=" * 70)
    print("RECOMENDACAO POR TAREFA")
    print("=" * 70)
    for r in recomendacoes:
        print(f"  [{r['tarefa']}] -> {r['tecnica_recomendada']}")
        print(f"     {r['justificativa']}")
    print("=" * 70 + "\n")

    return recomendacoes
