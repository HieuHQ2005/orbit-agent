from __future__ import annotations

import os
import json
from typing import List, Dict, Any

import requests
from dsp.modules.lm import LM


class OpenAIChatLM(LM):
    """Minimal OpenAI Chat Completions adapter for dsp/dspy LM interface.

    Returns a list of completion strings for a given prompt.
    """

    def __init__(
        self,
        model: str,
        api_key: str | None,
        temperature: float = 0.0,
        max_tokens: int = 400,
        api_base: str | None = None,
    ):
        super().__init__(model)
        self.provider = "openai"
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.api_base = api_base or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.kwargs["temperature"] = temperature
        self.kwargs["max_tokens"] = max_tokens

    def basic_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")

        url = f"{self.api_base}/chat/completions"
        payload = {
            "model": self.kwargs["model"],
            "messages": [
                {"role": "system", "content": "You are a concise, direct startup advisor."},
                {"role": "user", "content": prompt},
            ],
            "temperature": kwargs.get("temperature", self.kwargs.get("temperature", 0.0)),
            "max_tokens": kwargs.get("max_tokens", self.kwargs.get("max_tokens", 400)),
            "n": kwargs.get("n", self.kwargs.get("n", 1)),
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        resp.raise_for_status()
        return resp.json()

    def __call__(self, prompt: str, only_completed: bool = True, return_sorted: bool = False, **kwargs) -> List[str]:
        data = self.basic_request(prompt, **kwargs)
        choices = data.get("choices", [])
        out: List[str] = []
        for ch in choices:
            msg = ch.get("message", {})
            content = msg.get("content")
            if content:
                out.append(content)
        if not out and "error" in data:
            raise RuntimeError(f"OpenAI error: {data['error']}")
        if not out:
            # Fallback to an empty string to avoid crashes
            out = [""]
        return out


class OllamaLM(LM):
    """Minimal Ollama generate adapter for dsp/dspy LM interface.

    Uses /api/generate (non-streaming) and returns a single completion string.
    """

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434",
        temperature: float = 0.0,
        max_tokens: int = 400,
    ):
        super().__init__(model)
        self.provider = "ollama"
        self.base_url = base_url.rstrip("/")
        self.kwargs["temperature"] = temperature
        self.kwargs["max_tokens"] = max_tokens

    def basic_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.kwargs["model"],
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.kwargs.get("temperature", 0.0)),
                "num_predict": kwargs.get("max_tokens", self.kwargs.get("max_tokens", 400)),
            },
        }
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()

    def __call__(self, prompt: str, only_completed: bool = True, return_sorted: bool = False, **kwargs) -> List[str]:
        data = self.basic_request(prompt, **kwargs)
        text = data.get("response", "")
        return [text]
