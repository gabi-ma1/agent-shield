import requests


class Target:
    """Adapter that sends a message to a target agent's HTTP endpoint and returns its reply.

    Expects the endpoint to accept POST {"message": str, "history": [...],
    "system_prompt_override": str | None} and return {"reply": str}. The override field is
    only used during the re-verification stage, against targets that opt in to supporting it
    (see demo_target/vulnerable_bot.py) — it lets AgentShield prove a proposed hardened system
    prompt actually closes the gap, without needing write access to the target's real
    production config. Adjust this adapter if your target's API shape differs.
    """

    def __init__(
        self,
        url: str,
        timeout: float = 30.0,
        system_prompt_override: str | None = None,
    ):
        self._url = url
        self._timeout = timeout
        self._system_prompt_override = system_prompt_override

    def send(self, message: str, history: list[dict]) -> str:
        response = requests.post(
            self._url,
            json={
                "message": message,
                "history": history,
                "system_prompt_override": self._system_prompt_override,
            },
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.json()["reply"]
