# Architecture — GuardianLLM Lite

## System overview
GuardianLLM Lite is an ADK 2.0 graph `Workflow` that takes a target agent's project folder as input, runs it through a deterministic secret/PII scan, then routes clean inputs through two specialized LLM agents (an injection scanner and a privilege analyzer), and finally compiles all findings into a single structured audit report. The same logic is also packaged as an Antigravity Skill so it can be triggered by natural language inside any Antigravity project.

## Component diagram (ASCII)
```
[Target agent's repo: agent.py, SKILL.md files, hooks.json, pyproject.toml]
        |
        | local file read (intake)
        v
[intake_node]  (deterministic — parses structure, extracts system prompt + tool defs)
        |
        v
[security_screen_node]  (deterministic — regex scan for hardcoded secrets/keys)
        |
        ├── secrets found ──────────────► [reporting_node] ──► audit_report.md
        |
        └── clean ──► [injection_scanner_agent]  (LlmAgent — tests system prompt against
                              |                    known injection patterns)
                              v
                       [privilege_analyzer_agent]  (LlmAgent — reviews tool defs for
                              |                       over-broad permissions)
                              v
                       [reporting_node]  (deterministic — compiles findings)
                              v
                       audit_report.md
```

## Data flow
1. Developer points the auditor at a target agent's project folder (path provided as workflow input, or triggered via the Antigravity Skill on the currently open project).
2. `intake_node` reads `agent.py`, any `.agents/skills/*/SKILL.md`, `.agents/hooks.json`, and `pyproject.toml`, extracting the system prompt(s), tool function signatures, and declared dependencies into a structured in-memory representation.
3. `security_screen_node` runs deterministic regex checks for common secret patterns (API keys, AWS-style credentials, hardcoded passwords) — this never invokes the LLM, mirroring the course's pre-LLM screen pattern.
4. If secrets are found, the workflow short-circuits straight to `reporting_node` and flags the finding as critical — no need to spend LLM calls analyzing a repo that already fails on the most basic check.
5. If clean, the structured prompt and tool list pass to `injection_scanner_agent`, an `LlmAgent` instructed to test the target's system prompt against known jailbreak/injection patterns and report susceptibility with reasoning.
6. The same data passes to `privilege_analyzer_agent`, an `LlmAgent` instructed to review each tool's parameters and docstring for over-broad permissions (e.g. unscoped file paths, shell execution without validation).
7. `reporting_node` (deterministic) compiles all findings — secret-scan result, injection-scan result, privilege-analysis result — into a single `audit_report.md` with a severity-ranked summary at the top.

## Key interfaces
- **Workflow entry point**: `app = App(name="guardianllm_lite", root_agent=root_workflow)` — discoverable by `agents-cli playground`, `agents-cli run`, and ADK evaluation harnesses, exactly like the course's reference agents.
- **Skill entry point**: `.agents/skills/agent-security-audit/SKILL.md` — discovered automatically by Antigravity when a user's prompt matches the skill's description (e.g. "audit this agent for security issues").
- **Output interface**: a single `audit_report.md` written to the target project's root, plus the full structured findings returned as the workflow's final `Event` data (for programmatic use / tests).

## Security considerations
- [ ] `GEMINI_API_KEY` read only from environment variables (`.env`, gitignored) — never hardcoded, never logged.
- [ ] The auditor itself must pass its own audit (dogfooding) — no hardcoded secrets in `app/agent.py`, no over-privileged tools beyond local file reads required for intake.
- [ ] Input validation on the intake node — target folder path is validated before any file read; no arbitrary shell execution is ever performed on the target repo's contents (we read and analyze, we do not execute target code).
- [ ] Findings reports never echo back the actual secret values found — only their location and type (e.g. "hardcoded API key detected on line 13"), to avoid the report itself becoming a leak vector.
