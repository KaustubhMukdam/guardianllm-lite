# Copyright 2026 Google LLC
# Mock LLM implementation to isolate integration tests from the live Gemini API

import json
from collections.abc import AsyncGenerator
from typing import Any

from google.adk.models import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types


class MockLlm(BaseLlm):
    model: str = "mock-model"

    async def generate_content_async(
        self, llm_request: Any, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        # Extract system instructions
        system_instruction = ""
        config = getattr(llm_request, "config", None)
        if config and hasattr(config, "system_instruction"):
            instr = config.system_instruction
            if hasattr(instr, "parts") and instr.parts:
                system_instruction = "".join(
                    getattr(p, "text", "") or "" for p in instr.parts
                )
            elif isinstance(instr, str):
                system_instruction = instr

        # Route response based on which scanner agent is calling
        if "prompt injection" in system_instruction.lower():
            mock_data = {
                "susceptibility": "High",
                "findings": ["Mocked susceptibility: prompt vulnerability found."],
                "reasoning": "Mocked analysis showing injection risk.",
            }
        else:
            mock_data = {
                "over_broad_permissions": "Yes",
                "findings": ["Mocked privilege: tool execution allowed."],
                "reasoning": "Mocked analysis showing privilege risk.",
            }

        json_str = json.dumps(mock_data)
        yield LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part.from_text(text=json_str)],
            ),
            partial=False,
        )
