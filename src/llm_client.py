"""
llm_client.py
=============

Cliente HTTP para a API REST do Ollama (Aula 05).

Encapsula a comunicacao com o servidor local do Ollama, expondo um metodo
unico `chat()` que recebe prompt + system + parametros e retorna um dict
padronizado com a resposta, contagem de tokens e tempo de execucao.

Variaveis de ambiente esperadas (.env):
    OLLAMA_HOST    - URL base do Ollama (default: http://localhost:11434)
    OLLAMA_MODEL   - Nome do modelo (default: gpt-oss:120b)
"""
from __future__ import annotations

import os
import time
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()


class LLMClientError(Exception):
    """Erro generico do cliente LLM."""


class LLMClient:
    """Cliente para a API REST do Ollama (`/api/chat`)."""

    def __init__(
        self,
        host: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 120,
        max_retries: int = 3,
    ) -> None:
        self.host = (host or os.getenv("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "gpt-oss:120b")
        self.timeout = timeout
        self.max_retries = max_retries
        self.endpoint = f"{self.host}/api/chat"

    # ------------------------------------------------------------------ #
    # API publica
    # ------------------------------------------------------------------ #
    def chat(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 512,
    ) -> dict:
        """
        Envia uma mensagem ao modelo e retorna a resposta padronizada.

        Args:
            prompt:      mensagem do usuario.
            system:      system prompt (persona) opcional.
            temperature: criatividade do modelo (0.0 a 1.0).
            max_tokens:  limite de tokens da resposta.

        Returns:
            dict com as chaves:
                - resposta        (str)
                - tokens_prompt   (int)
                - tokens_resposta (int)
                - tempo_ms        (int)
        """
        if not prompt or not prompt.strip():
            raise LLMClientError("prompt vazio")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": float(temperature),
                "num_predict": int(max_tokens),
            },
        }

        start = time.perf_counter()
        data = self._post_with_retry(payload)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        message = data.get("message", {}) or {}
        return {
            "resposta": (message.get("content") or "").strip(),
            "tokens_prompt": int(data.get("prompt_eval_count", 0)),
            "tokens_resposta": int(data.get("eval_count", 0)),
            "tempo_ms": elapsed_ms,
        }

    # ------------------------------------------------------------------ #
    # Helpers internos
    # ------------------------------------------------------------------ #
    def _post_with_retry(self, payload: dict) -> dict:
        """POST com retry exponencial em falhas transitorias."""
        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    self.endpoint, json=payload, timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout as exc:
                last_error = exc
                wait = 2 ** attempt
                print(f"[LLMClient] timeout (tentativa {attempt}/{self.max_retries}) - aguardando {wait}s")
                time.sleep(wait)
            except requests.exceptions.RequestException as exc:
                last_error = exc
                # 4xx nao deve ser repetido
                status = getattr(exc.response, "status_code", None)
                if status and 400 <= status < 500:
                    raise LLMClientError(f"erro HTTP {status}: {exc}") from exc
                wait = 2 ** attempt
                print(f"[LLMClient] erro {exc} (tentativa {attempt}/{self.max_retries}) - aguardando {wait}s")
                time.sleep(wait)

        raise LLMClientError(f"todas as tentativas falharam: {last_error}")

    # ------------------------------------------------------------------ #
    # Diagnostico
    # ------------------------------------------------------------------ #
    def health_check(self) -> bool:
        """Verifica se o servidor Ollama esta respondendo."""
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=5)
            return r.status_code == 200
        except requests.exceptions.RequestException:
            return False
