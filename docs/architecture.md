# AgentShield — Architecture

## Pipeline: Recon → Adaptive Attack → Verify → Harden → Re-Verify

```
   ┌────────────────────────┐
   │  CLI (cli.py)           │
   │  agentshield run ...    │
   └──────────┬──────────────┘
              │
              v
   ┌────────────────────────────────┐
   │  Stage 1: Recon (recon.py)      │
   │  One neutral probe message to   │
   │  the target; Nemotron summa-    │
   │  rizes its apparent persona,    │
   │  tools, and guardrails.         │
   └──────────┬──────────────────────┘
              │  recon summary feeds the attacker's first move
              v
   ┌─────────────────────────────────────────────┐
   │  Stage 2-3: Adaptive Attack + Verify          │
   │  (attacker.py + judge.py)                     │
   │                                                │
   │  loop (up to max_turns):                       │
   │    attacker (Nemotron) picks next message,      │
   │      given full transcript + last verdict        │
   │    -> sent to Target (target.py)                  │
   │    -> judge (Nemotron) scores: succeeded?, 0-4     │
   │    stop early on success                            │
   └──────────┬────────────────────────────────────┘
              │  if attack succeeded
              v
   ┌─────────────────────────────────────┐
   │  Stage 4: Harden (harden.py)          │
   │  Given the worst turn + (optionally)   │
   │  the target's known original system     │
   │  prompt, Nemotron proposes either a       │
   │  full hardened rewrite or a generic        │
   │  guardrail addendum.                        │
   └──────────┬──────────────────────────────────┘
              │  if a full hardened prompt was produced
              v
   ┌──────────────────────────────────────┐
   │  Stage 5: Re-Verify                    │
   │  (attacker.run_reverification)          │
   │  Re-runs the SAME attack goal against    │
   │  the target, this time with the hardened  │
   │  prompt injected via system_prompt_        │
   │  override. Reports whether the fix           │
   │  actually held.                                │
   └──────────┬──────────────────────────────────────┘
              v
   ┌──────────────────────┐
   │  Report (report.py)    │
   │  .md (human-readable)   │
   │  .json (structured,      │
   │  for CI use)               │
   └──────────────────────────┘
```

## Attack goals (v1)

1. **System prompt extraction** — get the target to reveal its hidden instructions.
2. **Jailbreak** — get the target to ignore its stated constraints/persona.
3. **Tool-calling abuse** — get the target to invoke a tool it exposes in an unauthorized way
   (e.g. call a "delete" or "send_email" tool it shouldn't for this user). This is the goal
   that specifically targets *agents*, not just raw chat models — see Differentiation below.
4. **Data exfiltration** — get the target to leak data it was told to keep private (a planted
   secret in the demo target's context).

Each goal has its own attacker system prompt (see `attacker.py::GOALS`).

## Why an adaptive loop, not a static prompt list

Static jailbreak lists (e.g. "DAN prompts") are brittle and get patched. AgentShield's attacker
reads the target's actual last response and reasons about *why* an attempt failed, then picks a
different strategy (e.g. roleplay framing, multi-step distraction, encoding tricks, claiming
authority) — same as a human red-teamer would.

## Why Harden + Re-Verify, not just a report

A report that says "you're vulnerable" is easy to produce and easy to ignore. Re-running the
exact same attack against the proposed fix, and showing the severity actually dropped, is what
turns AgentShield from a scanner into something closer to an autonomous fix-and-confirm loop —
mirroring the "detect → remediate → verify" pattern used by incident-response tooling, applied
here to agent security instead of infrastructure.

**Known limitation:** Re-Verify only works against targets that opt in to accepting a
`system_prompt_override` field for testing (see `target.py`, `demo_target/vulnerable_bot.py`).
It cannot patch an arbitrary black-box production endpoint you don't control — for a real
target, the operator would run AgentShield against a staging copy of their own agent, or
integrate it in CI where AgentShield has access to the actual prompt/config.

## Nebius / NVIDIA integration

- `nebius_client.py` wraps the OpenAI-compatible Nebius Token Factory endpoint.
- Every stage's reasoning (recon summary, attacker, judge, hardening proposal) is a separate
  call to an NVIDIA Nemotron model on Nebius — set via `NEBIUS_MODEL` in `.env` (check the
  current Nebius Studio model catalog for the exact slug of the Nemotron variant you have
  access to).

## Demo target

`demo_target/vulnerable_bot.py` is a deliberately weak toy FastAPI chatbot used only so the
demo video has something to attack. It has:
- A system prompt (`demo_target/system_prompt.txt`) containing a fake secret ("internal refund
  code") and a fake `issue_refund` tool policy.
- Support for `system_prompt_override` in its `/chat` endpoint, purely so AgentShield's
  Re-Verify stage has something to test against end to end.

This is **not** shipped as a real product — it exists purely so AgentShield has a safe,
self-owned target to demonstrate against.

## Differentiation vs. existing tools (garak, PyRIT, promptfoo, Lakera, HiddenLayer)

| | garak / PyRIT / promptfoo | AgentShield |
|---|---|---|
| What's tested | The base LLM, mostly static probe categories | Full agents, including tool-calling behavior |
| Attack strategy | Mostly fixed prompt/probe lists | Live multi-turn attacker that adapts to responses |
| Output | Vulnerability report | Report **+ proposed fix + proof the fix works** |
| Audience | ML/security researchers comfortable with a CLI library | Self-serve: point at a URL, get a report |

## Track & positioning

- **Track: Best Apps and Agents** (not Coding/Agentic — that track requires agents that write,
  run, and test code in Token Factory Sandboxes, which AgentShield does not do; entering it
  there would risk failing the Stage 1 pass/fail gate).

## Status / decision log

- 2026-09-04: Track chosen: Coding / Agentic (later found to be wrong — see below). Idea
  chosen: AgentShield (autonomous adaptive red-teaming for AI agents), over "Sentinel"
  (behavioral ransomware detection) and a plain repo-runner agent.
- 2026-09-05: Read the official hackathon rules page. Corrected track to **Best Apps and
  Agents** — Track 1 (Coding/Agentic) specifically requires agents that write/run/test code in
  Token Factory Sandboxes, which doesn't match AgentShield's design.
- 2026-09-10: Locked **v2 pipeline** (Recon → Adaptive Attack → Verify → Harden → Re-Verify),
  adding the Harden and Re-Verify stages on top of the original attack/report loop. Motivated
  by (a) the realization that garak, a similar tool, is already an NVIDIA project — so the
  differentiator had to sharpen toward agent/tool-calling security plus a closed detect-fix-
  verify loop, not "red-teaming" in general, and (b) wanting a demo structure comparable to
  what won a different agent hackathon (an infra incident-response agent that verified its own
  fix worked, not just reported the problem).
