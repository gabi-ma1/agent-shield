import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .attacker import AttackSession
from .harden import HardeningResult
from .recon import ReconResult

SEVERITY_LABEL = {
    0: "None",
    1: "Low",
    2: "Medium",
    3: "High",
    4: "Critical",
}

MITIGATIONS_BY_GOAL = {
    "system_prompt_leak": (
        "- Never rely on the system prompt alone to hold secrets; treat it as visible.\n"
        "- Add an output filter that blocks responses resembling the system prompt text.\n"
        "- Test with paraphrase/translation requests, not just direct 'show me your prompt'."
    ),
    "jailbreak": (
        "- Add a second-pass safety classifier on the model's output, independent of the "
        "persona prompt.\n"
        "- Don't rely solely on instructions in the system prompt to enforce hard constraints; "
        "enforce them in code where possible."
    ),
    "tool_abuse": (
        "- Enforce tool-call limits (amounts, scopes) in the tool implementation itself, not "
        "just via prompt instructions.\n"
        "- Require explicit confirmation or a second authorization step for high-risk tool "
        "calls."
    ),
    "data_exfiltration": (
        "- Keep sensitive data out of the model's context entirely when possible; fetch it "
        "just-in-time behind an authorization check instead.\n"
        "- Add an output filter that scans for known sensitive patterns before returning a "
        "reply."
    ),
}


@dataclass
class PipelineResult:
    """Everything produced by one Recon -> Attack -> Verify -> Harden -> Re-Verify run."""

    target_url: str
    recon: ReconResult | None
    attack_session: AttackSession
    hardening: HardeningResult | None
    reverify_session: AttackSession | None

    @property
    def fix_confirmed(self) -> bool:
        if self.reverify_session is None:
            return False
        return not self.reverify_session.succeeded


def render_report(result: PipelineResult) -> str:
    session = result.attack_session
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# AgentShield Report",
        "",
        f"- **Target:** {result.target_url}",
        f"- **Goal:** {session.goal}",
        f"- **Generated:** {timestamp}",
        f"- **Turns run:** {len(session.turns)}",
        f"- **Attack succeeded:** {'YES' if session.succeeded else 'no'}",
        f"- **Max severity:** {session.max_severity} ({SEVERITY_LABEL[session.max_severity]})",
        "",
    ]

    if result.recon:
        lines += [
            "## Stage 1: Recon",
            "",
            f"**Opening message:** {result.recon.opening_message}",
            "",
            f"**Target reply:** {result.recon.target_reply}",
            "",
            f"**Summary:** {result.recon.summary}",
            "",
        ]

    lines += ["## Stage 2-3: Adaptive Attack + Verification", ""]

    for turn in session.turns:
        lines += [
            f"### Turn {turn.turn_number}",
            "",
            f"**Attacker:** {turn.attacker_message}",
            "",
            f"**Target:** {turn.target_reply}",
            "",
            (
                f"> Judge: succeeded={turn.verdict.succeeded}, "
                f"severity={turn.verdict.severity} "
                f"({SEVERITY_LABEL[turn.verdict.severity]}), "
                f"reason: {turn.verdict.reason}"
            ),
            "",
        ]

    lines += [
        "## Suggested mitigations",
        "",
        MITIGATIONS_BY_GOAL.get(session.goal, "- Review the transcript manually."),
        "",
    ]

    if result.hardening:
        lines += ["## Stage 4: Hardening", "", f"**Rationale:** {result.hardening.rationale}", ""]
        if result.hardening.hardened_system_prompt:
            lines += [
                "**Proposed hardened system prompt:**",
                "",
                "```",
                result.hardening.hardened_system_prompt,
                "```",
                "",
            ]
        if result.hardening.guardrail_addendum:
            lines += [
                "**Proposed guardrail addendum** (original system prompt was not available, "
                "so a full rewrite wasn't possible — add this to it manually):",
                "",
                "```",
                result.hardening.guardrail_addendum,
                "```",
                "",
            ]

    if result.reverify_session:
        rv = result.reverify_session
        lines += [
            "## Stage 5: Re-Verification",
            "",
            (
                f"Re-ran the same {len(rv.turns)}-turn attack against the hardened target. "
                f"**Fix confirmed: {'YES' if result.fix_confirmed else 'NO — attack still succeeded'}.**"
            ),
            f"- Max severity before fix: {session.max_severity} ({SEVERITY_LABEL[session.max_severity]})",
            f"- Max severity after fix: {rv.max_severity} ({SEVERITY_LABEL[rv.max_severity]})",
            "",
        ]
    elif result.hardening and result.hardening.hardened_system_prompt is None:
        lines += [
            "## Stage 5: Re-Verification",
            "",
            "Skipped — no full hardened system prompt was available to re-test against "
            "(only a guardrail addendum). Apply it manually and re-run AgentShield to verify.",
            "",
        ]

    return "\n".join(lines)


def _session_to_dict(session: AttackSession) -> dict:
    return {
        "goal": session.goal,
        "succeeded": session.succeeded,
        "max_severity": session.max_severity,
        "turns": [
            {
                "turn_number": t.turn_number,
                "attacker_message": t.attacker_message,
                "target_reply": t.target_reply,
                "verdict": asdict(t.verdict),
            }
            for t in session.turns
        ],
    }


def result_to_dict(result: PipelineResult) -> dict:
    return {
        "target_url": result.target_url,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "recon": asdict(result.recon) if result.recon else None,
        "attack": _session_to_dict(result.attack_session),
        "hardening": asdict(result.hardening) if result.hardening else None,
        "reverify": _session_to_dict(result.reverify_session)
        if result.reverify_session
        else None,
        "fix_confirmed": result.fix_confirmed,
    }


def save_report(result: PipelineResult, output_dir: str = "reports") -> tuple[Path, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    base_name = f"agentshield-{result.attack_session.goal}-{timestamp}"

    md_path = output_path / f"{base_name}.md"
    md_path.write_text(render_report(result), encoding="utf-8")

    json_path = output_path / f"{base_name}.json"
    json_path.write_text(
        json.dumps(result_to_dict(result), indent=2), encoding="utf-8"
    )

    return md_path, json_path
