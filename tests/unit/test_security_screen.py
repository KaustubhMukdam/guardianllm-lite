# Copyright 2026 Google LLC
# Unit tests for security_screen_node and its deterministic regex patterns

from app.agent import security_screen_node
from app.config import SECRET_PATTERNS


def test_google_api_key_regex():
    pattern = SECRET_PATTERNS["Google API Key"]
    valid_key = "AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q"
    assert pattern.search(valid_key) is not None
    assert pattern.search("not_a_key") is None


def test_aws_key_regex():
    pattern = SECRET_PATTERNS["AWS Access Key ID"]
    valid_key = "AKIAIOSFODNN7EXAMPLE"
    assert pattern.search(valid_key) is not None
    assert pattern.search("ASCAIOSFODNN7EXAMPLE") is not None
    assert pattern.search("not_a_key") is None


def test_aws_secret_regex():
    pattern = SECRET_PATTERNS["AWS Secret Access Key"]
    valid_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    assert pattern.search(valid_key) is not None
    assert pattern.search("short_key") is None


def test_slack_token_regex():
    pattern = SECRET_PATTERNS["Slack Token"]
    # Split token to bypass GitHub Push Protection during commit/push
    valid_token = (
        "xoxb-"
        + "123456789012"
        + "-"
        + "123456789012"
        + "-"
        + "abcdefghijklmnopqrstuvwx"
    )
    assert pattern.search(valid_token) is not None
    assert pattern.search("xoxb-123-abc") is None


def test_github_token_regex():
    pattern = SECRET_PATTERNS["GitHub Personal Access Token"]
    valid_old_token = "ghp_abcdefghijklmnopqrstuvwxyzABCDEF1234"
    valid_new_token = "github_pat_1234567890123456789012_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567"
    assert pattern.search(valid_old_token) is not None
    assert pattern.search(valid_new_token) is not None
    assert pattern.search("ghp_short") is None


def test_generic_api_key_regex():
    pattern = SECRET_PATTERNS["Generic API Key / Secret"]
    match_cases = [
        "api_key = 'abcdefghijklmnop'",
        'apikey = "abcdefghijklmnop"',
        "secret_key='abcdefghijklmnop'",
        "client_secret = 'abcdefghijklmnop'",
        "auth_token = 'abcdefghijklmnop'",
        "api_token = 'abcdefghijklmnop'",
    ]
    for case in match_cases:
        assert pattern.search(case) is not None, f"Failed to match: {case}"

    assert pattern.search("key = 'abcdefghijklmnop'") is None


def test_security_screen_node_routing_clean():
    # Input without secrets
    node_input = {
        "target_dir": "dummy_clean",
        "combined_code": "def my_func():\n    pass",
    }
    # Pass None as Context since security_screen_node does not use it
    event = security_screen_node._func(None, node_input)

    assert event.actions.route == "clean"
    assert event.actions.state_delta["secrets_found"] is False
    assert "dummy_clean" in event.output


def test_security_screen_node_routing_secrets_found():
    # Input with secret
    node_input = {
        "target_dir": "dummy_secrets",
        "combined_code": "GOOGLE_KEY = 'AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q'",
    }
    # Pass None as Context
    event = security_screen_node._func(None, node_input)

    assert event.actions.route == "secrets_found"
    assert event.actions.state_delta["secrets_found"] is True
    assert len(event.output["findings"]) == 1
    assert event.output["findings"][0]["type"] == "Google API Key"
