# Nebius x NVIDIA Global AI Hackathon

Working repo for https://nebiusglobalaihackathon.devpost.com/

## Deadline
**October 30, 2026, 10:00am PDT**

## What this hackathon wants
Build a working AI system on open, independent infrastructure using **NVIDIA open-source models served through Nebius**.

### Track (pick one)
- [ ] ~~Coding / Agentic~~ (rejected — that track requires agents that write/run/test code in
  Token Factory Sandboxes; AgentShield doesn't, so it would likely fail the Stage 1 pass/fail
  gate there)
- [x] Best Apps / Agents
- [ ] Personal AI
- [ ] Physical AI (requires a ≥1 min clip of hardware actually operating)

### Allowed tech
- NVIDIA Nemotron 3 (Ultra / Nano / Super)
- Other NVIDIA open-source models: NemoClaw, OpenShell, Hermes Agent, GROOT, Cosmos, Sonic
- Nebius Token Factory, AI Cloud, Serverless Endpoints, Serverless Jobs
- Optional: Tavily (separate $3,000 prize for best use)

## Submission checklist
- [ ] Pick track
- [ ] Build project using an NVIDIA model on Nebius (Token Factory or AI Cloud)
- [ ] Write project description (what it does, how it works)
- [ ] Deploy a working demo URL (not required for Physical AI track)
- [ ] Record demo video (≤3 min, YouTube, with audio, must mention Nebius + NVIDIA model usage)
- [ ] Push public repo (GitHub/GitLab/Bitbucket) with an OSS license
- [ ] Write this README with setup + run instructions
- [ ] Write feedback on Nebius tools / NVIDIA tech used (counts for "Most Valuable Feedback" prize)

## Judging criteria
1. **Technological Implementation** — how effectively Nebius/NVIDIA models are integrated
2. **Design** — complete product experience, not just proof-of-concept
3. **Potential Impact** — solves a real problem for a real audience
4. **Quality of Idea** — creative, non-obvious application

## Project idea: AgentShield

**Autonomous security pipeline for AI agents: attack them, then prove the fix works.**

Every team at this hackathon is shipping an LLM agent with tool access. That's the new attack
surface: prompt injection, jailbreaks, system-prompt extraction, tool-calling abuse, data
exfiltration through the agent itself. Most "AI security" tooling (including NVIDIA's own
[garak](https://github.com/NVIDIA/garak)) evaluates the base model with mostly static probes —
it tells you something is wrong, not whether your fix actually worked.

AgentShield runs a 5-stage pipeline against a target agent/chatbot endpoint:

**Recon → Adaptive Attack → Verify → Harden → Re-Verify**

1. **Recon** — a quick, neutral probe to learn the target's apparent persona/tools/guardrails.
2. **Adaptive Attack** — a multi-turn attacker agent (not a static jailbreak list) that reads
   the target's actual replies and changes strategy turn by turn, pursuing one goal: system
   prompt leak, jailbreak, tool-calling abuse, or data exfiltration.
3. **Verify** — an independent judge model scores each turn (succeeded? how severe, 0-4?).
4. **Harden** — if the attack succeeded, a model proposes a concrete hardened system prompt
   (or a guardrail addendum, if the original prompt isn't known) **and a runnable code patch**
   (e.g. an output filter or a tool-call guard) — prompt instructions alone aren't a reliable
   security boundary, so the fix is also enforced in code, not just requested of the model.
5. **Re-Verify** — re-runs the same attack against the hardened version and reports whether the
   fix actually closed the gap — the same "detect → fix → confirm it's fixed" loop that makes
   incident-response tooling credible, applied to agent security instead of infrastructure.

**Intended, authorized use only:** testing agents/chatbots you own or are explicitly authorized
to test (e.g. your own hackathon submission, before shipping it).

**Differentiation from garak/PyRIT/promptfoo:** those are research libraries for evaluating a
raw LLM with mostly static probes. AgentShield targets full **agents with tool access** (the
"tool_abuse" goal), runs a live adaptive attacker instead of a fixed prompt list, and — unlike
any of them — closes the loop by re-testing its own proposed fix.

**Scaling as a product:** positioned as a continuous security regression check — re-run
automatically whenever a team changes their agent's system prompt or tools (like a CI/CD
security gate), not just a one-off scan. Target buyer: any team shipping an agent to
production, which after this hackathon is a large and growing group.

### Architecture
See [docs/architecture.md](docs/architecture.md).

## Setup

1. Get a Nebius Token Factory API key: sign up at
   [tokenfactory.nebius.com](https://tokenfactory.nebius.com) (Google/GitHub login works, no
   sales call), then go to **Project Settings -> API Keys** and create one. New accounts get
   trial credits. Never commit this key — it only ever goes in your local `.env`, never in
   code or in `.env.example`.
2. Confirm the model slug you want in the
   [Token Factory model catalog](https://tokenfactory.nebius.com/models/catalog) — availability
   can change; `nvidia/nemotron-3-super-120b-a12b` is what's set by default.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# fill in NEBIUS_API_KEY (and NEBIUS_MODEL if different) in .env
```

## Running it

1. Start the toy vulnerable target (for demo/dev purposes only):

```bash
python demo_target/vulnerable_bot.py
```

2. In another terminal, run the full pipeline against it. Passing `--system-prompt-file`
   (pointing at the demo target's own known prompt) enables the Harden + Re-Verify stages —
   without it, AgentShield still attacks and reports, but only proposes a generic guardrail
   addendum instead of a testable full rewrite:

```bash
python -m src.agentshield.cli run \
  --target-url http://127.0.0.1:8000/chat \
  --goal data_exfiltration \
  --system-prompt-file demo_target/system_prompt.txt \
  --max-turns 8
```

Other goals: `system_prompt_leak`, `jailbreak`, `tool_abuse`. Add `--skip-harden` to stop after
the attack/verification stages.

3. Find the generated reports under `reports/` — a human-readable `.md` and a structured
   `.json` (for CI integration / programmatic use) per run.

## License
MIT (see [LICENSE](LICENSE)) — required for submission (public repo, OSS license).
