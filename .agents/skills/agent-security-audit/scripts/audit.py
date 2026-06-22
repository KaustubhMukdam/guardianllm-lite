# ruff: noqa: E402
# Copyright 2026 Google LLC
# Helper script to execute GuardianLLM Lite security audit from the Antigravity Skill

import asyncio
import os
import sys

# Setup path to import app.agent from the project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", "..", "..", ".."))
sys.path.insert(0, project_root)

# Load env variables
from dotenv import load_dotenv

load_dotenv(os.path.join(project_root, ".env"))

from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agent import app


async def main():
    target_path = sys.argv[1] if len(sys.argv) > 1 else "."
    target_path = os.path.abspath(target_path)

    if not os.path.isdir(target_path):
        print(f"Error: Target path {target_path} is not a directory.")
        sys.exit(1)

    print(f"Auditing agent project at: {target_path}...")

    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(
        app_name="guardianllm_lite", user_id="skill_audit"
    )

    report_content = None
    try:
        async for event in runner.run_async(
            user_id="skill_audit",
            session_id=session.id,
            new_message=types.Content(
                role="user",
                parts=[types.Part.from_text(text=target_path)],
            ),
        ):
            # The final event will yield the markdown report
            if event.output is not None:
                report_content = event.output
    except Exception as e:
        print(f"Error during audit run: {e}")
        sys.exit(1)

    if report_content:
        # Print the report, safely encoding emojis for Windows console
        try:
            print("\n" + report_content)
        except UnicodeEncodeError:
            encoding = sys.stdout.encoding or "utf-8"
            print(
                "\n"
                + str(report_content)
                .encode(encoding, errors="replace")
                .decode(encoding)
            )

        print(
            f"\n[Success] Audit complete. Report written to: {os.path.join(target_path, 'audit_report.md')}"
        )
    else:
        print("\n[Error] Audit failed to generate report.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
