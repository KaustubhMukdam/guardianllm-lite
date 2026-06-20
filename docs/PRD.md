# PRD — GuardianLLM Lite

## Problem statement
Teams are vibe-coding and deploying AI agents faster than they can review them for security. An agent that has tool access (file reads, shell execution, payment actions, API calls) inherits a new attack surface: hardcoded secrets left in during rapid prototyping, prompt injection via untrusted input (tool outputs, user descriptions, retrieved documents), and over-privileged tools that can do more than the agent's stated purpose requires. This is exactly the failure class the Kaggle/Google "5-Day AI Agents" course's own Day 4 security lab was built to defend against — but most teams have no repeatable way to check whether their *own* agent has these issues before shipping it.

## Target users
- Developers vibe-coding ADK/agentic projects who want a pre-commit-style check on their agent's security posture before deploying.
- Hackathon/capstone participants (like us) who want to verify their own agent doesn't leak secrets or expose injectable surfaces.
- Small engineering teams adopting agentic AI internally who need a lightweight, no-cost audit step before granting an agent production tool access.

## Core features (MVP)
- [ ] **Intake node** — reads a target agent's project folder (`agent.py`, any `SKILL.md` files, `hooks.json`, `pyproject.toml`) and produces a structured summary of system prompt, tools, and permissions.
- [ ] **Security screen node (deterministic)** — regex/static-analysis pass for hardcoded API keys, credentials, and obvious secrets, before any LLM call is made. Mirrors the Day 4 course pattern: catch what doesn't need a model.
- [ ] **Injection scanner agent (LLM)** — given the target's system prompt, tests it against a battery of known prompt-injection patterns and reports susceptibility.
- [ ] **Privilege analyzer agent (LLM)** — reviews the target's tool definitions for over-broad permissions (e.g. unscoped file/shell access, missing input validation).
- [ ] **Reporting node (deterministic)** — compiles all findings into a single structured `audit_report.md`.
- [ ] **Packaged as an Antigravity Skill** — installable as `.agents/skills/agent-security-audit/`, so any Antigravity user can run "audit this agent" as a slash-triggered skill on their own project.

## Nice-to-have (post-MVP)
- [ ] Hosted read-only demo (FastAPI on Render/HF Spaces free tier) so judges can try the auditor without local setup, with our own key kept server-side.
- [ ] STRIDE-style threat classification layer on top of the raw findings (Spoofing/Tampering/Repudiation/Information Disclosure/DoS/Elevation of Privilege), matching the course's own threat-modeling skill pattern.
- [ ] MCP server that lets the auditor pull a target repo directly instead of requiring local file access (explicitly out of scope for MVP — not demonstrated in the codelabs we completed).

## Non-goals
- This is not a general-purpose static analysis tool (it does not replace Semgrep/Bandit; it focuses specifically on agent-shaped risks: prompts, tools, permissions).
- This does not automatically fix vulnerabilities — it reports them. Remediation is left to the developer.
- This does not require or use Google Cloud Agent Runtime, billing, or any paid service.
- This does not require the target agent to be built with ADK — but ADK/agents-cli projects get the richest analysis since the intake node understands that structure natively.

## Success metrics
- A developer can point the auditor at a sample vulnerable agent (e.g. our own earlier GuardianLLM code, used as a test subject) and get a structured report identifying at least the 3 known injected issues in under 2 minutes.
- The Antigravity Skill triggers correctly when a user types a natural-language audit request, without needing to remember an exact command.
- A judge can clone the repo, set their own `GEMINI_API_KEY`, and run `agents-cli playground` to interact with the auditor within 5 minutes, per the README setup steps.

## Constraints
- Time: ~17 days (deadline July 6, 2026, 11:59 PM PT)
- Cost: Free tier only — no GCP billing, no paid APIs beyond a personal Gemini API key
- Tech: Must demonstrate at least 3 of the course's 6 key concepts (ADK/multi-agent, Security features, Agent skills/CLI are our chosen 3)
- Submission: GitHub repo + setup instructions (live deploy optional, not required by rubric)
