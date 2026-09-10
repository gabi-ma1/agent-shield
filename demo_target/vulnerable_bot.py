"""A deliberately weak toy chatbot, used ONLY as a self-owned target for AgentShield demos.

Do not deploy this anywhere real — it exists purely so the attacker agent has something
authorized to attack for the hackathon demo video.

Run: python demo_target/vulnerable_bot.py
"""

import os
import sys

from dotenv import load_dotenv
from fastapi import FastAPI
from openai import OpenAI
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from agentshield.config import Config  # noqa: E402

load_dotenv()

# Kept in a separate file (not just this constant) so it can also be passed to
# `agentshield run --system-prompt-file demo_target/system_prompt.txt`, letting the demo run
# the full Harden + Re-Verification stages against a system prompt AgentShield actually knows.
_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
SYSTEM_PROMPT = open(_PROMPT_PATH, encoding="utf-8").read()

app = FastAPI(title="Vulnerable demo bot (AgentShield target)")
_config = Config.from_env()
_client = OpenAI(api_key=_config.nebius_api_key, base_url=_config.nebius_base_url)
_model = _config.nebius_model


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    system_prompt_override: str | None = None


class ChatResponse(BaseModel):
    reply: str


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    # Accepting a caller-supplied system prompt only makes sense because this is a throwaway
    # demo target we own, used to prove AgentShield's Re-Verification stage end to end. A real
    # target would never expose this.
    active_prompt = request.system_prompt_override or SYSTEM_PROMPT
    messages = [{"role": "system", "content": active_prompt}, *request.history]
    messages.append({"role": "user", "content": request.message})

    completion = _client.chat.completions.create(
        model=_model,
        messages=messages,
        temperature=0.7,
        max_tokens=400,
    )
    reply = completion.choices[0].message.content or ""
    return ChatResponse(reply=reply)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
