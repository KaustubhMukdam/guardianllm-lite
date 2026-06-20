# Folder Structure — GuardianLLM Lite

```
guardianllm-lite/
├── app/
│   ├── agent.py              # ADK 2.0 Workflow: intake, security_screen, injection_scanner,
│   │                         # privilege_analyzer, reporting nodes/agents — the core graph
│   ├── config.py             # Model name, regex patterns for secret detection, thresholds
│   └── fast_api_app.py        # (optional) wraps the workflow for the hosted demo, if built
├── .agents/
│   ├── skills/
│   │   └── agent-security-audit/
│   │       └── SKILL.md      # Packaged skill — makes the auditor reusable in any Antigravity project
│   └── hooks.json            # (optional) pre-tool-use validation, matching course pattern
├── tests/
│   ├── test_security_screen.py   # outcome-based tests for the deterministic secret scanner
│   ├── test_agent.py              # tests for the full workflow routing logic
│   └── eval/
│       ├── datasets/
│       │   └── basic-dataset.json   # synthetic vulnerable/clean agent scenarios for LLM-as-judge eval
│       └── eval_config.yaml         # judge metrics: detection accuracy, false-positive rate
├── docs/                       # all documentation lives here
│   ├── project_context.md
│   ├── PRD.md
│   ├── tech_stack.md
│   ├── architecture.md
│   ├── folder_structure.md
│   ├── tasks.md
│   ├── design_prompt.md
│   └── learnings.md
├── sample_target_agent/        # a deliberately vulnerable mock agent used to demo/test the auditor
│   └── agent.py                # contains a hardcoded mock key + an injectable prompt, on purpose
├── pyproject.toml
├── .env.example                # template only — real .env is gitignored
├── .gitignore
└── README.md                   # setup instructions for judges (this is the submission's main entry point)
```

## Naming conventions
- ADK nodes: snake_case functions decorated with `@node` (`security_screen_node`, `reporting_node`)
- LLM agents: snake_case variables holding `LlmAgent` instances (`injection_scanner_agent`, `privilege_analyzer_agent`)
- Skill directories: kebab-case (`agent-security-audit`), matching the course's own `stride-threat-model` convention
- Test files: `test_<module>.py`, one per node/agent group
- Config constants: UPPER_SNAKE_CASE in `config.py` (e.g. `SECRET_PATTERNS`, `MODEL_NAME`)
