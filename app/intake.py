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


def parse_target_directory(target_dir: str) -> dict:
    """Parses a target agent's directory to extract system instructions, tools, skills, and hooks."""
    target_dir = target_dir.replace('"', "").replace("'", "").strip()

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
