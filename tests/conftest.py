# Copyright 2026 Google LLC
# Test configuration to initialize paths and load environment variables

import os
import sys

from dotenv import load_dotenv

# Ensure project root is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load env variables
load_dotenv(os.path.join(project_root, ".env"))
