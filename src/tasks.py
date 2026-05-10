"""
tasks.py
========

Definicao das 4 tarefas do dominio de e-commerce (Aula 08):

    1. classificacao_sentimento   (classificacao)
    2. extracao_dados             (extracao)
    3. sumarizacao_review         (sumarizacao)
    4. geracao_resposta           (geracao)

Cada tarefa segue o esquema descrito no enunciado do checkpoint:
    - nome
    - tipo
    - instrucao
    - formato_output
    - exemplos_fewshot
    - passos_cot
    - persona
"""
from __future__ import annotations

from typing import List, Dict


TAREFAS: List[Dict] = [
    # ------------------------------------------------------------------ #
    # 1. CLASSIFICACAO DE SENTIMENTO
    # ------------------------------------------------------------------ #
    {
        "nome": "classificacao_sentimento",
        "tipo": "classificacao",
        "instrucao": (
            "Classifique a avaliacao de um cliente de e-commerce em uma "
            "das 4 categorias: POSITIVO, NEGATIVO, NEUTRO ou MISTO."
        ),
        "formato_output": (
            "Responda APENAS com a categoria em letras maiusculas, "
            "sem pontuacao, sem explicacao."
        ),
        "exemplos_fewshot": [
            {"input": "Adorei o produto, chegou rapido!", "output": "POSITIVO"},
            {"input": "Veio quebrado, pessima experiencia.", "output": "NEGATIVO"},
            {"input": "Bom preco, mas qualidade media.", "output": "MISTO"},
        ],
        "passos_cot": [
            "Identifique aspectos positivos mencionados",
            "Identifique aspectos negativos mencionados",
            "Compare a intensidade entre positivos e negativos",
            "Decida a classificacao final",
        ],
        "persona": "analista_cx",
    },

    # ------------------------------------------------------------------ #
    # 2. EXTRACAO DE DADOS ESTRUTURADOS
    # ------------------------------------------------------------------ #
    {
        "nome": "extracao_dados",
        "tipo": "extracao",
        "instrucao": (
            "Extraia do ticket de suporte as seguintes informacoes em "
            "formato JSON: produto, preco e defeito. Se algum campo nao "
            "estiver presente, use null."
        ),
        "formato_output": (
            'Responda APENAS com um JSON valido no formato: '
            '{"produto": "...", "preco": "...", "defeito": "..."}'
        ),
        "exemplos_fewshot": [
            {
                "input": "Notebook Dell de R$3500 com pixels mortos na tela",
                "output": {"produto": "Notebook Dell", "preco": "R$3500", "defeito": "pixels mortos"},
            },
            {
                "input": "Comprei o fone JBL por 250 reais e veio sem o cabo",
                "output": {"produto": "Fone JBL", "preco": "R$250", "defeito": "sem cabo"},
            },
        ],
        "passos_cot": [
            "Localize o nome do produto na mensagem",
            "Localize o preco mencionado (com ou sem R$)",
            "Identifique qual e o defeito relatado",
            "Monte o JSON com os tres campos",
        ],
        "persona": "engenheiro_dados",
    },

    # ------------------------------------------------------------------ #
    # 3. SUMARIZACAO DE REVIEWS
    # ------------------------------------------------------------------ #
    {
        "nome": "sumarizacao_review",
        "tipo": "sumarizacao",
        "instrucao": (
            "Resuma a avaliacao do cliente em UMA UNICA frase de no "
            "maximo 20 palavras, capturando o ponto principal."
        ),
        "formato_output": "Responda apenas com a frase do resumo, sem aspas.",
        "exemplos_fewshot": [
            {
                "input": (
                    "Comprei essa cafeteira mes passado. O design e bonito "
                    "e a entrega foi rapida, mas o cafe sai morno e o "
                    "reservatorio vaza apos 3 usos. Decepcionante."
                ),
                "output": "Cafeteira com design bonito e entrega rapida, mas cafe morno e reservatorio que vaza.",
            },
            {
                "input": (
                    "Tenis confortavel desde o primeiro uso, parece de "
                    "qualidade superior ao preco. Recomendo."
                ),
                "output": "Tenis confortavel e de qualidade superior ao preco pago.",
            },
        ],
        "passos_cot": [
            "Identifique o produto avaliado",
            "Liste os aspectos positivos",
            "Liste os aspectos negativos",
            "Condense tudo em uma unica frase",
        ],
        "persona": "analista_cx",
    },

    # ------------------------------------------------------------------ #
    # 4. GERACAO DE RESPOSTA SAC
    # ------------------------------------------------------------------ #
    {
        "nome": "geracao_resposta",
        "tipo": "geracao",
        "instrucao": (
            "Redija uma resposta cordial e profissional do SAC para a "
            "reclamacao do cliente. A resposta deve: (a) reconhecer o "
            "problema, (b) pedir desculpas, (c) propor uma solucao "
            "concreta (troca, estorno ou suporte tecnico)."
        ),
        "formato_output": (
            "Responda APENAS com o texto da mensagem, em portugues do "
            "Brasil, com no maximo 4 frases."
        ),
        "exemplos_fewshot": [
            {
                "input": "Meu liquidificador veio sem as laminas, paguei caro nisso!",
                "output": (
                    "Ola! Lamentamos muito o ocorrido com seu liquidificador. "
                    "Pedimos desculpas pelo transtorno e ja iremos providenciar "
                    "o envio das laminas faltantes em ate 2 dias uteis. Caso "
                    "prefira, podemos efetuar a troca ou o estorno integral."
                ),
            },
        ],
        "passos_cot": [
            "Identifique qual e o produto e o problema",
            "Decida o tom: empatico e profissional",
            "Escolha a solucao mais adequada (troca, estorno, suporte)",
            "Redija a resposta com no maximo 4 frases",
        ],
        "persona": "atendente_sac",
    },
]


def listar_tarefas() -> List[Dict]:
    """Retorna a lista completa de tarefas."""
    return TAREFAS


def buscar_tarefa(nome: str) -> Dict:
    """Busca uma tarefa pelo nome."""
    for t in TAREFAS:
        if t["nome"] == nome:
            return t
    raise KeyError(f"tarefa '{nome}' nao encontrada")
