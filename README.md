# Prompt Toolkit — Grupo NextGen

> Checkpoint 02 · FIAP · Prompt Engineering & Artificial Intelligence
> Toolkit em Python que aplica automaticamente as 4 técnicas de prompting
> (Zero-Shot, Few-Shot, Chain-of-Thought e Role Prompting) a tarefas de
> negócio do domínio de e-commerce, mede qualidade e custo de cada
> abordagem e gera um relatório comparativo com recomendação automática.

---

## Integrantes — Grupo NextGen

| Nome | RM |
|---|---|
| Gustavo Franzoti Gonçalves | 566983 |
| Lincoln Simão Pereira | 567284 |
| Maykon Santana Fonseca | 567041 |
| Nicolas Sakaue Nishimura | 567752 |

**Professor:** Jorge Luiz Gomes

---

## Visão Geral

O **Prompt Toolkit** recebe uma tarefa de domínio (classificação,
extração, sumarização ou geração), aplica as 4 técnicas de prompting,
mede:

- **Acurácia** (match exato, JSON estrutural ou keywords)
- **Custo** (tokens de prompt + tokens de resposta, via `tiktoken`)
- **Tempo** de resposta
- **Consistência** entre repetições com diferentes temperaturas

…e gera um relatório (CSV + 3 gráficos PNG) com recomendação automática
da melhor técnica para cada tarefa.

Tudo roda **local e gratuito** via Ollama com o modelo `gpt-oss:120b`.

---

## Estrutura do projeto

```
prompt-toolkit/
├── README.md                  # este arquivo
├── requirements.txt           # dependências Python
├── .env.example               # exemplo de variáveis de ambiente
├── .gitignore
├── main.py                    # ponto de entrada
├── src/
│   ├── __init__.py
│   ├── llm_client.py          # cliente Ollama (Aula 05)
│   ├── prompt_builder.py      # anatomia de prompts (Aula 05)
│   ├── techniques.py          # ZS, FS, CoT, Role (Aulas 06+07)
│   ├── tasks.py               # 4 tarefas do domínio (Aula 08)
│   ├── evaluator.py           # tokens, acurácia, consistência
│   └── report.py              # tabela + gráficos + recomendação
├── data/
│   ├── inputs.json            # 5 inputs reais por tarefa
│   └── examples.json          # exemplos few-shot adicionais
├── prompts/
│   ├── system_prompts.json    # personas detalhadas (Aula 07)
│   └── templates.json         # templates de prompt
├── output/
│   ├── resultados.csv         # gerado pelo toolkit
│   └── graficos/              # PNGs gerados pelo toolkit
└── docs/
    └── CP02_NextGen.pdf       # documentação ABNT do projeto
```

---

## Pré-requisitos

- **Python 3.10+**
- **Ollama** instalado e rodando localmente
  ([instalação oficial](https://ollama.com/download))
- O modelo `gpt-oss:120b` baixado:
  ```bash
  ollama pull gpt-oss:120b
  ```
- Servidor Ollama em execução:
  ```bash
  ollama serve
  ```
  Por padrão sobe em `http://localhost:11434`.

> **Sem API paga**: todo o processamento é local, conforme exigido
> pelo enunciado do checkpoint.

---

## Instalação

```bash
# 1. clonar o repositório
git clone https://github.com/<seu-usuario>/prompt-toolkit.git
cd prompt-toolkit

# 2. criar ambiente virtual
python -m venv .venv
source .venv/bin/activate         # Linux / macOS
# .venv\Scripts\activate           # Windows

# 3. instalar dependências
pip install -r requirements.txt

# 4. configurar variáveis de ambiente
cp .env.example .env
# (edite .env se o Ollama estiver em outro host/modelo)
```

---

## Como executar

Com o Ollama rodando:

```bash
python main.py
```

O sistema irá:

1. Verificar se o Ollama está respondendo (health check)
2. Para cada uma das 4 tarefas, aplicar as 4 técnicas em 5 inputs
   (4 × 4 × 5 = **80 chamadas ao LLM**)
3. Gerar `output/resultados.csv` com todas as métricas
4. Gerar três gráficos PNG em `output/graficos/`:
   - `acuracia.png` — barras agrupadas por técnica e tarefa
   - `custo.png` — tokens médios por técnica
   - `temperatura.png` — consistência por temperatura
5. Imprimir no terminal a tabela resumo + recomendação automática
6. Rodar teste de temperatura (0.1 / 0.5 / 1.0) no melhor prompt

---

## As 4 técnicas implementadas

| Técnica | Como funciona | Aula |
|---|---|---|
| **Zero-Shot** | Instrução direta + formato de saída, sem exemplos | 06 |
| **Few-Shot** | Adiciona 2–3 exemplos `Input → Output` antes da consulta | 06 |
| **Chain-of-Thought** | Instrui raciocínio passo a passo antes da resposta | 06 |
| **Role Prompting** | Define persona detalhada via `system prompt` | 07 |

Cada técnica é uma função em `src/techniques.py`. Adicionar uma nova é
trivial — basta seguir a assinatura `f(tarefa, input_dados) -> str` (ou
`-> (system, user)` para técnicas baseadas em system prompt).

---

## As 4 tarefas do domínio (e-commerce)

| Tarefa | Tipo | Saída esperada |
|---|---|---|
| `classificacao_sentimento` | Classificação | POSITIVO / NEGATIVO / NEUTRO / MISTO |
| `extracao_dados` | Extração | JSON `{produto, preco, defeito}` |
| `sumarizacao_review` | Sumarização | 1 frase de até 20 palavras |
| `geracao_resposta` | Geração | Resposta de SAC com até 4 frases |

Inputs reais em `data/inputs.json` (5 por tarefa, totalizando 20).

---

## Personas (Role Prompting)

`prompts/system_prompts.json` contém 4 personas detalhadas (experiência
+ especialidade + tom + limitações), conforme exigido pela Aula 07.

Personas incluídas:

- `analista_cx` — analista sênior de Customer Experience
- `engenheiro_dados` — engenheiro de dados especialista em NLP
- `atendente_sac` — atendente sênior de SAC
- `redator_marketing` — redator de marketing para e-commerce

---

## Output esperado

Após rodar `python main.py` com sucesso:

```
output/
├── resultados.csv                # ~80 linhas, uma por execução
└── graficos/
    ├── acuracia.png
    ├── custo.png
    └── temperatura.png
```

E no terminal, algo como:

```
======================================================================
RESUMO COMPARATIVO
======================================================================
                      tarefa            tecnica  acuracia_media  ...
   classificacao_sentimento          zero_shot           0.800
   classificacao_sentimento           few_shot           1.000
   classificacao_sentimento  chain_of_thought           1.000
   classificacao_sentimento     role_prompting           1.000
   ...
======================================================================
RECOMENDACAO POR TAREFA
======================================================================
  [classificacao_sentimento] -> few_shot
     acuracia=1.00, tokens_medio=12, tempo_medio=940ms
  [extracao_dados] -> few_shot
     acuracia=1.00, tokens_medio=42, tempo_medio=1080ms
  ...
```

---

## Documentação

A documentação completa em formato ABNT está em
[`docs/CP02_NextGen.pdf`](docs/CP02_NextGen.pdf), incluindo:

- Capa, sumário e referências
- Domínio e justificativa
- Diagrama de arquitetura
- Stack técnica
- Resultados (tabelas e gráficos)
- Guia de bolso (quando usar cada técnica)
- Reflexão final

---

## Troubleshooting

| Erro | Causa provável | Solução |
|---|---|---|
| `Ollama nao esta respondendo` | Servidor Ollama parado | `ollama serve` em outro terminal |
| `model 'gpt-oss:120b' not found` | Modelo não foi baixado | `ollama pull gpt-oss:120b` |
| Timeout em todas as chamadas | Modelo grande demais para a máquina | Trocar para `gpt-oss:20b` no `.env` |
| `ModuleNotFoundError: tiktoken` | Dependências não instaladas | `pip install -r requirements.txt` |

---

## Licença

Projeto acadêmico — uso educacional. © 2026 Grupo NextGen / FIAP.
