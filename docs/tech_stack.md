# Tech Stack — GuardianLLM Lite

## Agent framework
| Technology | Version | Why chosen |
|------------|---------|------------|
| Google ADK | 2.0 (graph Workflow API) | This is the exact framework the course taught (`Workflow`, `Edge`, `LlmAgent`, `@node`, `Context`, `Event`). Using the real 2.0 graph API — not a custom orchestration layer — directly satisfies the "Agent/Multi-agent system (ADK)" rubric concept and shows genuine course mastery rather than a from-scratch reimplementation. |
| `agents-cli` | latest via `uvx google-agents-cli` | Official scaffolding/lint/playground/eval/deploy tool taught across multiple codelabs. Used for scaffold, lint, and local playground testing. |
| Antigravity IDE | latest | The agentic IDE the entire course is built around. Used to drive development via natural-language prompts and to author/test the packaged Skill. |

## Model
| Technology | Why chosen |
|------------|------------|
| Gemini (via `GEMINI_API_KEY`) | Standard course authentication path (Google AI Studio key). Avoids GCP billing entirely — no Vertex AI / Application Default Credentials needed for local development and judging. |

## Language & testing
| Technology | Version | Why chosen |
|------------|---------|------------|
| Python | 3.11 | ADK 2.0 and `agents-cli` requirement. |
| Pytest | latest | Outcome-based security tests — assert on final report content and state, not on internal mocks, matching the course's own testing philosophy from the Day 4 secure-agentic-coding lab. |
| `uv` | latest | Package manager used consistently throughout the course codelabs for environment setup and dependency locking. |

## Security tooling
| Technology | Why chosen |
|------------|------------|
| Python `re` (regex) | Deterministic secret/PII detection before any LLM call — mirrors the course's pre-LLM security screen pattern (Day 4 expense agent), keeps detection of obvious leaks cheap and non-probabilistic. |
| (Optional) Semgrep | If time allows, add a pre-commit Semgrep scan on our *own* repo, matching the Day 4 lab exactly, as a demonstration of practicing what the tool preaches. |

## Packaging
| Technology | Why chosen |
|------------|------------|
| Antigravity Skill (`SKILL.md`) | Makes the auditor reusable inside the same tool every course participant and judge already has installed — directly satisfies "Agent skills (e.g. Agents CLI)" rubric concept, demonstrated live in the video. |

## Deployment (constrained)
| Technology | Why chosen |
|------------|------------|
| None required (GitHub repo submission) | Rubric explicitly allows a code repo with setup instructions instead of a live deploy. Chosen to avoid GCP billing entirely. |
| (Optional) Render or Hugging Face Spaces free tier | If we want a zero-setup demo for judges, a read-only FastAPI wrapper calling our own server-side key. Not required for a valid submission. |

## Alternatives considered
- **Custom MCP server for repo ingestion** — rejected for MVP. Only codelab we completed on MCP demonstrates *consuming* an existing server (Google Developer Knowledge MCP), not authoring one. Building one from scratch would be real, valid work, but it's unscaffolded by the course and risky given the 17-day timeline — kept as a nice-to-have, not a core concept we rely on.
- **Google Cloud Agent Runtime deployment** — rejected. Requires a billing-enabled GCP project, which violates our free-of-cost constraint. The rubric does not require live deployment.
- **LangGraph (from prior ResearchBench AI work)** — rejected for this project specifically, in favor of ADK 2.0, because the course's own rubric concept is literally named "Agent/Multi-agent system (ADK)" — using ADK directly removes any ambiguity about whether the concept was demonstrated.

## Known tradeoffs
- Judges need their own free Gemini API key to run the project locally (standard for every course lab — not unusual friction for this audience).
- Without the optional hosted demo, there is no zero-setup click-through; mitigated by a clear, tested README and a screen-recorded video walkthrough.
