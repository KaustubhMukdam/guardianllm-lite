---
name: agent-security-audit
description: Audit the current AI agent project for security vulnerabilities (hardcoded secrets, prompt injections, over-privileged tools). Use when user wants to audit this agent, check security posture, scan for hardcoded secrets, or runs security checks.
---

# Agent Security Audit

This skill allows you to audit the current agent project for security vulnerabilities, including:
1. Hardcoded secrets and API keys (deterministic regex scanning).
2. Prompt injection susceptibility in system instructions.
3. Over-privileged tools (filesystem/command execution risks).

## Workflows

1. **Verify environment**: Make sure `GEMINI_API_KEY` is set in the environment or `.env`.
2. **Execute the audit**: Run the audit script, passing the target project path (default is the current directory `.`).
   ```bash
   uv run python .agents/skills/agent-security-audit/scripts/audit.py .
   ```
3. **Review the findings**: The script will generate `audit_report.md` in the target project root. Open and read it to review the security posture and implement recommended mitigations.
