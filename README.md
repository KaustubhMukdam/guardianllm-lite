# GuardianLLM Lite

An ADK 2.0 multi-agent workflow that audits AI agents for security vulnerabilities — hardcoded secrets, prompt-injection-susceptible system prompts, and over-privileged tools — before they ship.

Built for Kaggle's **AI Agents: Intensive Vibe Coding Capstone Project**, track: **Agents for Business**.

## Why this exists

Teams are shipping AI agents faster than they can review them. An agent with tool access (file reads, shell execution, API calls) inherits real risk: hardcoded secrets left in during rapid prototyping, prompt injection via untrusted input, and tools with more permission than the agent's job requires. GuardianLLM Lite is a repeatable, automated check for exactly these issues — built using the same patterns Google's own course teaches for _defending_ agents, turned into a tool that _audits_ them.

## How it works

```
[target agent's repo]
        |
        v
  intake_node ───► security_screen_node (deterministic secret scan)
                          |
              secrets found ──► reporting_node ──► audit_report.md
                          |
                       clean
                          |
                          v
         injection_scanner_agent (LLM) ──► privilege_analyzer_agent (LLM)
                          |
                          v
                   reporting_node ──► audit_report.md
```

Full architecture details: [`docs/architecture.md`](docs/architecture.md)

## Course concepts demonstrated

| Concept                          | Where                                                                                   |
| -------------------------------- | --------------------------------------------------------------------------------------- |
| Agent / Multi-agent system (ADK) | `app/agent.py` — full ADK 2.0 graph `Workflow` with deterministic nodes and `LlmAgent`s |
| Security features                | `app/agent.py` (`security_screen_node`), `tests/test_security_screen.py`                |
| Agent skills (Agents CLI)        | `.agents/skills/agent-security-audit/SKILL.md` — installable in any Antigravity project |

## Setup (takes about 5 minutes)

**Prerequisites:** Python 3.11+, [`uv`](https://docs.astral.sh/uv/getting-started/installation/), a free [Google AI Studio API key](https://aistudio.google.com/app/apikey).

```bash
# 1. Clone the repo
git clone https://github.com/KaustubhMukdam/guardianllm-lite.git
cd guardianllm-lite

# 2. Set up your environment
cp .env.example .env
# edit .env and paste in your own GEMINI_API_KEY

# 3. Install dependencies
uv sync

# 4. Run the local playground
agents-cli playground
```

Open the printed URL (usually `http://127.0.0.1:8080/dev-ui/?app=app`), select the `app` folder, and point the auditor at `sample_target_agent/` — a deliberately vulnerable mock agent included in this repo for demo purposes.

## Running tests

```bash
uv run pytest tests/
```

## Project documentation

Full documentation, including the PRD, tech stack rationale, and task log, is in [`docs/`](docs/):

- [`docs/PRD.md`](docs/PRD.md) — problem statement, target users, scope
- [`docs/tech_stack.md`](docs/tech_stack.md) — every technology choice and why
- [`docs/architecture.md`](docs/architecture.md) — full system design and data flow
- [`docs/folder_structure.md`](docs/folder_structure.md) — repo layout explained

## A note on cost and access

This project runs entirely free of cost — no Google Cloud billing, no Agent Runtime deployment. It requires only a free Gemini API key, the same one every participant in the underlying Kaggle course already obtained. No API keys or secrets are committed to this repository.
