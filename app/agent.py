# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ast
import os
import re

from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.apps import App
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from google.adk.models import Gemini
from google.adk.workflow import JoinNode, Workflow, node
from google.genai import types
from pydantic import BaseModel, Field

from app.config import MODEL_NAME, SECRET_PATTERNS


# Define Structured Output Schemas for the LLM Agents
class InjectionScanResult(BaseModel):
    susceptibility: str = Field(
        description="Susceptibility level: High, Medium, or Low"
    )
    findings: list[str] = Field(
        default_factory=list,
        description="Specific vulnerability findings in the prompt",
    )
    reasoning: str = Field(
        description="Detailed technical reasoning behind the findings"
    )


class PrivilegeAnalysisResult(BaseModel):
    over_broad_permissions: str = Field(
        description="Are permissions over-broad? Yes, No, or Suspicious"
    )
    findings: list[str] = Field(
        default_factory=list,
        description="Specific privilege/permission issues found in tools",
    )
    reasoning: str = Field(
        description="Detailed explanation of the tool permissions issues"
    )


# 1. Intake Node (Deterministic)
# Parses target folder to extract system instructions, tools, skills, and hooks
@node
def intake_node(ctx: Context, node_input: str | types.Content) -> dict:
    # Handle string input or types.Content input from the user
    if isinstance(node_input, str):
        target_dir = node_input.strip()
    else:
        parts = getattr(node_input, "parts", None)
        if parts:
            target_dir = "".join(
                getattr(part, "text", "") or "" for part in parts
            ).strip()
        else:
            target_dir = ""

    # Clean quotes if any
    target_dir = target_dir.replace('"', "").replace("'", "")

    if not os.path.isdir(target_dir):
        return {
            "error": f"Target directory not found: {target_dir}",
            "target_dir": target_dir,
        }

    # Search for agent files
    agent_files = []
    app_agent_path = os.path.join(target_dir, "app", "agent.py")
    root_agent_path = os.path.join(target_dir, "agent.py")

    if os.path.isfile(app_agent_path):
        agent_files.append(app_agent_path)
    if os.path.isfile(root_agent_path):
        agent_files.append(root_agent_path)

    if not agent_files:
        # Fallback to searching for any .py file if standard ones aren't found
        for file in os.listdir(target_dir):
            if file.endswith(".py") and file != "fast_api_app.py":
                agent_files.append(os.path.join(target_dir, file))

    if not agent_files:
        return {
            "error": "No Python agent files (.py) found in target directory.",
            "target_dir": target_dir,
        }

    # Read files and parse instructions and tools
    parsed_instructions = []
    parsed_tools = []
    combined_code = ""

    for agent_file in agent_files:
        try:
            with open(agent_file, encoding="utf-8") as f:
                code_content = f.read()
                combined_code += (
                    f"\n# File: {os.path.relpath(agent_file, target_dir)}\n"
                    + code_content
                )

                # Parse AST
                try:
                    tree = ast.parse(code_content)
                    for n in ast.walk(tree):
                        # Extract function-based tools
                        if isinstance(n, ast.FunctionDef):
                            docstring = ast.get_docstring(n) or "No docstring provided."
                            args = [arg.arg for arg in n.args.args]
                            sig = f"def {n.name}({', '.join(args)})"

                            # Extract lines of code for the tool
                            lines = code_content.splitlines()[
                                n.lineno - 1 : n.end_lineno
                            ]
                            tool_code = "\n".join(lines)

                            parsed_tools.append(
                                {
                                    "name": n.name,
                                    "signature": sig,
                                    "docstring": docstring,
                                    "code": tool_code,
                                }
                            )

                        # Extract Agent instruction parameters
                        elif isinstance(n, ast.Call):
                            if isinstance(n.func, ast.Name) and n.func.id in (
                                "Agent",
                                "LlmAgent",
                            ):
                                for kw in n.keywords:
                                    if kw.arg == "instruction":
                                        if isinstance(kw.value, ast.Constant):
                                            parsed_instructions.append(kw.value.value)
                except Exception:
                    pass
        except Exception:
            pass

    # Fallback instruction extraction via regex if AST missed variables
    if not parsed_instructions:
        instr_matches = re.findall(
            r"instruction\s*=\s*(?:'''(.*?)'''|r'''(.*?)'''|\"\"\"(.*?)\"\"\"|r\"\"\"(.*?)\"\"\"|'(.*?)'|\"(.*?)\")",
            combined_code,
            re.DOTALL,
        )
        for m in instr_matches:
            val = next((item for item in m if item), "")
            if val:
                parsed_instructions.append(val)

    # Read skills and hooks
    skills = []
    hooks = None

    skills_dir = os.path.join(target_dir, ".agents", "skills")
    if os.path.isdir(skills_dir):
        for root_dir, _, files in os.walk(skills_dir):
            for file in files:
                if file.endswith(".md"):
                    file_path = os.path.join(root_dir, file)
                    try:
                        with open(file_path, encoding="utf-8") as f:
                            skills.append(
                                {
                                    "name": os.path.relpath(file_path, target_dir),
                                    "content": f.read(),
                                }
                            )
                    except Exception:
                        pass

    hooks_file = os.path.join(target_dir, ".agents", "hooks.json")
    if os.path.isfile(hooks_file):
        try:
            with open(hooks_file, encoding="utf-8") as f:
                hooks = f.read()
        except Exception:
            pass

    pyproject_file = os.path.join(target_dir, "pyproject.toml")
    pyproject_content = ""
    if os.path.isfile(pyproject_file):
        try:
            with open(pyproject_file, encoding="utf-8") as f:
                pyproject_content = f.read()
        except Exception:
            pass

    return {
        "target_dir": target_dir,
        "instructions": list(set(parsed_instructions)),
        "tools": parsed_tools,
        "skills": skills,
        "hooks": hooks,
        "pyproject": pyproject_content,
        "combined_code": combined_code,
    }


# 2. Security Screen Node (Deterministic)
# Regex scan for hardcoded secrets, API keys, credentials
@node
def security_screen_node(ctx: Context, node_input: dict) -> Event:
    if "error" in node_input:
        return Event(
            output=node_input,
            actions=EventActions(route="secrets_found"),
        )

    combined_code = node_input.get("combined_code", "")
    target_dir = node_input.get("target_dir", "")
    findings = []

    # Process secrets scanning line by line to get line numbers
    lines = combined_code.splitlines()
    current_file = "Unknown"

    for i, line in enumerate(lines):
        # File marker comment added by intake
        if line.startswith("# File: "):
            current_file = line.replace("# File: ", "").strip()
            continue

        for name, pattern in SECRET_PATTERNS.items():
            matches = pattern.finditer(line)
            for _ in matches:
                # We report the match location but NOT the actual secret content
                # to prevent leaking the secret in the audit report
                findings.append(
                    {
                        "file": current_file,
                        "line": i + 1,
                        "type": name,
                        "message": f"Potential {name} detected at line {i + 1} in {current_file}",
                    }
                )

    if findings:
        return Event(
            output={
                "target_dir": target_dir,
                "secrets_found": True,
                "findings": findings,
            },
            actions=EventActions(
                route="secrets_found",
                state_delta={"target_dir": target_dir, "secrets_found": True},
            ),
        )

    # Formatting prompt input for downstream LLM agents
    instructions_str = (
        "\n---\n".join(node_input.get("instructions", [])) or "None declared."
    )
    tools_str = ""
    for t in node_input.get("tools", []):
        tools_str += f"\n- Name: {t['name']}\n  Signature: {t['signature']}\n  Docstring: {t['docstring']}\n  Code Snippet:\n```python\n{t['code']}\n```\n"

    skills_str = ""
    for s in node_input.get("skills", []):
        skills_str += f"\nSkill File: {s['name']}\n```markdown\n{s['content']}\n```\n"

    hooks_str = node_input.get("hooks", "") or "None declared."

    prompt_for_agents = f"""# Target Agent to Audit: {target_dir}

## Declared System Instructions:
{instructions_str}

## Declared Tools:
{tools_str or "No tools declared."}

## Declared Skills:
{skills_str or "No skills declared."}

## Declared Hooks:
```json
{hooks_str}
```
"""
    return Event(
        output=prompt_for_agents,
        actions=EventActions(
            route="clean",
            state_delta={"target_dir": target_dir, "secrets_found": False},
        ),
    )


# Conditionally choose model (Model Seam)
if os.environ.get("USE_MOCK_LLM") == "TRUE":
    from app.mock_llm import MockLlm

    scanner_model = MockLlm()
    analyzer_model = MockLlm()
else:
    scanner_model = Gemini(
        model=MODEL_NAME,
        retry_options=types.HttpRetryOptions(attempts=3),
    )
    analyzer_model = Gemini(
        model=MODEL_NAME,
        retry_options=types.HttpRetryOptions(attempts=3),
    )


# 3. Injection Scanner Agent (LLM)
# Analyzes susceptibility to prompt injection and jailbreaking
injection_scanner_agent = LlmAgent(
    name="injection_scanner_agent",
    model=scanner_model,
    instruction="""You are a security auditor specializing in prompt injection and jailbreaking vulnerabilities in AI agents.
Your task is to analyze the target agent's system instructions and evaluate if it is susceptible to prompt injection.

Look for:
- Lack of instruction defense (e.g. not telling the agent to ignore user requests to change its role/system instructions).
- Contradictory instructions.
- Overly submissive instructions (e.g. "always follow user instructions").
- Dynamic parts of the prompt that might contain untrusted inputs without proper sanitization.

You must output a structured JSON response matching the schema provided, indicating:
1. Susceptibility level ("High", "Medium", or "Low")
2. Specific findings (detailed list of vulnerability points)
3. Reasoning (technical explanation of the susceptibility)
""",
    output_schema=InjectionScanResult,
)


# 4. Privilege Analyzer Agent (LLM)
# Analyzes tools for over-broad permissions
privilege_analyzer_agent = LlmAgent(
    name="privilege_analyzer_agent",
    model=analyzer_model,
    instruction="""You are a security auditor specializing in analyzing tool permissions and privilege levels in AI agents.
Your task is to analyze the target agent's tools (function signatures, docstrings, and code implementation if available) for over-broad permissions.

Look for:
- Tools that execute shell commands or run arbitrary code (`subprocess`, `eval`, `exec`, `os.system`).
- Tools that read or write to arbitrary filesystem paths without sandboxing or restriction.
- Tools that make arbitrary HTTP/network requests without domain whitelisting.
- Tools with broad write permissions (e.g., databases, external APIs) without proper input sanitization.
- Tools that do more than the agent's stated purpose requires.

You must output a structured JSON response matching the schema provided, indicating:
1. Over-broad permissions ("Yes", "No", or "Suspicious")
2. Specific findings (detailed list of privilege issues)
3. Reasoning (technical explanation of why permissions are too broad)
""",
    output_schema=PrivilegeAnalysisResult,
)


# 5. Join Node
join_node = JoinNode(name="join_node")


# 6. Reporting Node (Deterministic)
# Compiles findings into audit_report.md
@node
def reporting_node(ctx: Context, node_input: dict) -> str:
    target_dir = ctx.state.get("target_dir", "")

    # If the intake/scan failed or secrets were found
    if "error" in node_input:
        report_md = f"""# GuardianLLM Lite Audit Report
Target Directory: `{target_dir}`
Status: **FAILED (Scan Error)**

## Error Details
{node_input["error"]}
"""
    elif node_input.get("secrets_found"):
        report_md = f"""# GuardianLLM Lite Audit Report
Target Directory: `{target_dir}`
Status: 🛑 **CRITICAL FINDINGS**

## Summary
The audit has been short-circuited because critical, hardcoded secrets or credentials were detected in the source code.
No LLM scan was performed on the instructions or privileges because this code violates basic safety standards.

## 🛑 Hardcoded Secrets ({len(node_input["findings"])} found)
"""
        for f in node_input["findings"]:
            report_md += (
                f"- **{f['type']}** found at line `{f['line']}` in file `{f['file']}`\n"
            )

        report_md += """
---
*Recommendation: Immediately revoke the exposed secrets and move them to environment variables (.env) or a secret manager.*
"""
    else:
        # Successful clean run through LLM agents
        injection_result_raw = node_input.get("injection_scanner_agent", {})
        privilege_result_raw = node_input.get("privilege_analyzer_agent", {})

        # Reconstruct typed schemas
        try:
            injection_result = InjectionScanResult(**injection_result_raw)
        except Exception:
            injection_result = InjectionScanResult(
                susceptibility="Unknown",
                findings=[],
                reasoning="Error parsing injection scan output.",
            )

        try:
            privilege_result = PrivilegeAnalysisResult(**privilege_result_raw)
        except Exception:
            privilege_result = PrivilegeAnalysisResult(
                over_broad_permissions="Unknown",
                findings=[],
                reasoning="Error parsing privilege analysis output.",
            )

        # Determine overall severity
        overall_status = "🟢 CLEAN PASS"
        if (
            injection_result.susceptibility == "High"
            or privilege_result.over_broad_permissions == "Yes"
        ):
            overall_status = "🛑 CRITICAL / HIGH SUSCEPTIBILITY"
        elif (
            injection_result.susceptibility == "Medium"
            or privilege_result.over_broad_permissions == "Suspicious"
        ):
            overall_status = "⚠️ WARNING / MEDIUM SUSCEPTIBILITY"

        report_md = f"""# GuardianLLM Lite Audit Report
Target Directory: `{target_dir}`
Overall Status: **{overall_status}**

---

## 🔍 Deterministic Scanner
- **Secrets & API Keys**: ✅ Clean (No hardcoded secrets detected)

---

## 🛡️ Injection Scanner Agent
- **Susceptibility Level**: `{injection_result.susceptibility}`

### Findings:
"""
        if injection_result.findings:
            for f in injection_result.findings:
                report_md += f"- ⚠️ {f}\n"
        else:
            report_md += "- No major prompt injection vulnerabilities detected in system instructions.\n"

        report_md += f"""
### Technical Reasoning:
{injection_result.reasoning}

---

## 🔑 Privilege Analyzer Agent
- **Over-Broad Permissions**: `{privilege_result.over_broad_permissions}`

### Findings:
"""
        if privilege_result.findings:
            for f in privilege_result.findings:
                report_md += f"- 🔑 {f}\n"
        else:
            report_md += "- No over-privileged tools detected.\n"

        report_md += f"""
### Technical Reasoning:
{privilege_result.reasoning}
"""

    # Save the report to target directory
    if target_dir and os.path.isdir(target_dir):
        report_path = os.path.join(target_dir, "audit_report.md")
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_md)
        except Exception as e:
            report_md += f"\n\n*Warning: Failed to save report to file system: {e!s}*"

    # Yield output event for user interface
    yield Event(
        output=report_md,
        content=types.Content(
            role="model", parts=[types.Part.from_text(text=report_md)]
        ),
    )


# Wire the Graph
root_agent = Workflow(
    name="guardianllm_lite",
    edges=[
        ("START", intake_node),
        (intake_node, security_screen_node),
        # Conditional routing based on the route emitted by security_screen_node
        (
            security_screen_node,
            {
                "secrets_found": reporting_node,
                "clean": (injection_scanner_agent, privilege_analyzer_agent),
            },
        ),
        ((injection_scanner_agent, privilege_analyzer_agent), join_node),
        (join_node, reporting_node),
    ],
)

app = App(
    root_agent=root_agent,
    name="guardianllm_lite",
)
