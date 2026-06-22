# Copyright 2026 Google LLC
# Integration tests for the full GuardianLLM Lite agent workflow

import os

import pytest
from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agent import app


@pytest.mark.asyncio
async def test_audit_vulnerable_agent():
    """Verify that auditing the vulnerable agent triggers the secret short-circuit path."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    target_path = os.path.join(project_root, "sample_target_agent")

    # Remove any existing report from previous runs
    report_file = os.path.join(target_path, "audit_report.md")
    if os.path.exists(report_file):
        os.remove(report_file)

    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(
        app_name="guardianllm_lite", user_id="test_user"
    )

    report_content = None
    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=types.Content(
            role="user",
            parts=[types.Part.from_text(text=target_path)],
        ),
    ):
        if event.output is not None:
            report_content = event.output

    assert report_content is not None, "Failed to get audit report"
    assert "CRITICAL FINDINGS" in report_content
    assert "Google API Key" in report_content
    assert os.path.exists(report_file), "Audit report file was not written to disk"

    # Clean up
    if os.path.exists(report_file):
        os.remove(report_file)


@pytest.mark.asyncio
async def test_audit_clean_agent():
    """Verify that auditing a clean directory runs the LLM scans successfully."""
    import asyncio
    import logging
    from google.genai.errors import ClientError, ServerError
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    target_path = os.path.join(project_root, "app")
    
    # Remove any existing report from previous runs
    report_file = os.path.join(target_path, "audit_report.md")
    if os.path.exists(report_file):
        os.remove(report_file)
        
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(
        app_name="guardianllm_lite", user_id="test_user"
    )
    
    report_content = None
    attempts = 3
    for attempt in range(attempts):
        try:
            async for event in runner.run_async(
                user_id="test_user",
                session_id=session.id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=target_path)],
                ),
            ):
                if event.output is not None:
                    report_content = event.output
            break
        except (ClientError, ServerError, Exception) as e:
            # Catch general API errors/exceptions and retry unless it's the last attempt
            if attempt == attempts - 1:
                raise e
            logging.warning(
                f"Gemini API rate limited or server error, retrying in 12s... (attempt {attempt + 1}/{attempts})"
            )
            await asyncio.sleep(12)
            
    assert report_content is not None, "Failed to get audit report"
    assert "Secrets & API Keys" in report_content
    assert "Clean" in report_content
    assert "## 🛡️ Injection Scanner Agent" in report_content
    assert "## 🔑 Privilege Analyzer Agent" in report_content
    assert os.path.exists(report_file), "Audit report file was not written to disk"
    
    # Clean up
    if os.path.exists(report_file):
        os.remove(report_file)
