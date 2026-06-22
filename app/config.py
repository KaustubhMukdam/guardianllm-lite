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

import re

# Model configuration (preserve model selection where possible)
MODEL_NAME = "gemini-2.5-flash"

# Regex patterns for common secrets and credentials
SECRET_PATTERNS = {
    "Google API Key": re.compile(r"AIzaSy[A-Za-z0-9-_]{35}"),
    "AWS Access Key ID": re.compile(r"ASCA[0-9A-Z]{16}|AKIA[0-9A-Z]{16}"),
    "AWS Secret Access Key": re.compile(
        r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{40}(?![A-Za-z0-9+/])"
    ),
    "Generic Private Key": re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----"),
    "Slack Token": re.compile(r"xox[bapr]-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{24}"),
    "GitHub Personal Access Token": re.compile(
        r"ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}"
    ),
    "Generic API Key / Secret": re.compile(
        r"(?i)(api_key|apikey|secret_key|client_secret|auth_token|api_token)\s*=\s*['\"][a-zA-Z0-9\-_]{16,}['\"]"
    ),
}
