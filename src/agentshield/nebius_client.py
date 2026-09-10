from openai import OpenAI

from .config import Config


class NebiusClient:
    """Thin wrapper around the OpenAI-compatible Nebius Token Factory API."""

    def __init__(self, config: Config):
        self._config = config
        self._client = OpenAI(
            api_key=config.nebius_api_key,
            base_url=config.nebius_base_url,
        )

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.8,
        max_tokens: int = 800,
    ) -> str:
        response = self._client.chat.completions.create(
            model=self._config.nebius_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
