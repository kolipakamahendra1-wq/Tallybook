import httpx

from ..config import Settings, get_settings


class LLMError(RuntimeError):
    pass


class LLMClient:
    """Minimal provider interface: one call, text in, text out."""

    name = "base"

    def complete(self, system: str, prompt: str) -> str:
        raise NotImplementedError


def _post(url: str, timeout: float, **kwargs) -> dict:
    try:
        resp = httpx.post(url, timeout=timeout, **kwargs)
    except httpx.HTTPError as exc:
        raise LLMError(f"request to {url} failed: {exc}") from exc
    if resp.status_code >= 400:
        raise LLMError(f"{url} returned {resp.status_code}: {resp.text[:300]}")
    return resp.json()


class OllamaClient(LLMClient):
    name = "ollama"

    def __init__(self, s: Settings):
        self.s = s

    def complete(self, system: str, prompt: str) -> str:
        data = _post(
            f"{self.s.ollama_url}/api/chat",
            self.s.llm_timeout,
            json={
                "model": self.s.ollama_model,
                "stream": False,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                "options": {"temperature": 0.2, "repeat_penalty": 1.15, "num_predict": 400},
            },
        )
        return data["message"]["content"].strip()


class OpenAIClient(LLMClient):
    name = "openai"

    def __init__(self, s: Settings):
        if not s.openai_api_key:
            raise LLMError("OPENAI_API_KEY is not set")
        self.s = s

    def complete(self, system: str, prompt: str) -> str:
        data = _post(
            "https://api.openai.com/v1/chat/completions",
            self.s.llm_timeout,
            headers={"Authorization": f"Bearer {self.s.openai_api_key}"},
            json={
                "model": self.s.openai_model,
                "temperature": 0.2,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            },
        )
        return data["choices"][0]["message"]["content"].strip()


class AnthropicClient(LLMClient):
    name = "anthropic"

    def __init__(self, s: Settings):
        if not s.anthropic_api_key:
            raise LLMError("ANTHROPIC_API_KEY is not set")
        self.s = s

    def complete(self, system: str, prompt: str) -> str:
        data = _post(
            "https://api.anthropic.com/v1/messages",
            self.s.llm_timeout,
            headers={"x-api-key": self.s.anthropic_api_key, "anthropic-version": "2023-06-01"},
            json={
                "model": self.s.anthropic_model,
                "max_tokens": 600,
                "system": system,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        return data["content"][0]["text"].strip()


class FakeClient(LLMClient):
    """Deterministic stand-in for tests; optionally raises."""

    name = "fake"

    def __init__(self, reply: str = "Fake brief.", fail: bool = False):
        self.reply, self.fail, self.calls = reply, fail, 0

    def complete(self, system: str, prompt: str) -> str:
        self.calls += 1
        if self.fail:
            raise LLMError("fake failure")
        return self.reply


def get_client(settings: Settings | None = None) -> LLMClient:
    s = settings or get_settings()
    providers = {"ollama": OllamaClient, "openai": OpenAIClient, "anthropic": AnthropicClient}
    if s.llm_provider not in providers:
        raise LLMError(f"unknown LLM_PROVIDER '{s.llm_provider}' (use ollama, openai or anthropic)")
    return providers[s.llm_provider](s)
