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

from app.config import SECRET_PATTERNS


def scan_code_for_secrets(combined_code: str) -> list[dict]:
    """Scans code for hardcoded secrets based on defined regex patterns."""
    findings = []
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
    return findings
