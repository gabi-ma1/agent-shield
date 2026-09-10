import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    nebius_api_key: str
    nebius_base_url: str
    nebius_model: str

    @classmethod
    def from_env(cls) -> "Config":
        api_key = os.environ.get("NEBIUS_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "NEBIUS_API_KEY is not set. Copy .env.example to .env and fill it in."
            )
        return cls(
            nebius_api_key=api_key,
            nebius_base_url=os.environ.get(
                "NEBIUS_BASE_URL", "https://api.studio.nebius.com/v1"
            ),
            nebius_model=os.environ.get(
                "NEBIUS_MODEL", "nvidia/Llama-3_1-Nemotron-70B-Instruct"
            ),
        )
