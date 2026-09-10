# Ideas

Brainstorm de proyectos por track. Decisión final documentada en [architecture.md](architecture.md).

## Elegida: AgentShield (Best Apps and Agents)
Pipeline de seguridad autónomo (Recon → Ataque Adaptativo → Verificación → Endurecimiento →
Re-Verificación) contra agentes/chatbots de IA. Track corregido de "Coding/Agentic" a "Best
Apps and Agents" tras leer las reglas oficiales (Track 1 exige agentes que escriban/ejecuten
código en sandboxes, algo que no hacemos). Ver [architecture.md](architecture.md).

## Descartadas
- **Sentinel** (detección/contención de ransomware con razonamiento explicable): impacto muy visual
  e instantáneo, pero el uso del LLM corría riesgo de sentirse "bolted-on" sobre lo que es
  fundamentalmente detección conductual/telemetría.
- **Repo-to-Runnable** (agente que clona y deja corriendo cualquier repo): buen demo, pero menos
  diferenciado y sin conexión directa con seguridad, que era el interés del usuario.
- **Escáner + Auto-Parche de vulnerabilidades / Copiloto de triage SOC**: descartadas por ser
  espacios más trillados en hackathons de seguridad.

## Coding / Agentic
-

## Best Apps / Agents
-

## Personal AI
-

## Physical AI
-

## Notas sobre modelos NVIDIA disponibles en Nebius
- Nemotron 3 Ultra / Nano / Super — modelos de lenguaje de propósito general
- NemoClaw, OpenShell, Hermes Agent — orientados a agentes
- GROOT, Cosmos, Sonic — robótica / mundo físico / audio (revisar para Physical AI)
