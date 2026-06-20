"""Deterministic tests — no network, no API key, no hardware.

Run:  pip install pytest && PYTHONPATH=src pytest tests -q
Covers the logic that doesn't need the model: routing, the approval/destructive
gates, per-customer context isolation + linking, and capture dedup.
"""
import pytest

from jarvis import approval, context, router, store


@pytest.fixture(autouse=True)
def tmp_vault(tmp_path, monkeypatch):
    """Point the vault at a throwaway dir so tests don't touch real data."""
    monkeypatch.setattr(context, "VAULT", tmp_path / "vault")
    monkeypatch.setattr(context, "ACTIVE_FILE", tmp_path / "vault" / ".active")
    yield


def test_model_routing():
    assert router.choose_model("hey what time is it") == router.config.MODEL_FAST
    assert router.choose_model("write code to refactor the parser") == router.config.MODEL_HEAVY


def test_send_gate():
    assert approval.requires_approval("mcp__Slack__slack_send_message")
    assert not approval.requires_approval("mcp__fs__read_file")


def test_destructive_guard():
    assert approval.is_destructive("Bash", {"command": "rm -rf ~/stuff"})
    assert approval.is_destructive("Bash", {"command": "git push origin main --force"})
    assert not approval.is_destructive("Bash", {"command": "ls -la"})


def test_context_isolation_and_linking():
    context.switch("Acme Corp")
    assert context.active() == "acme-corp"
    context.set_link("code", "/tmp/acme")
    assert context.code_path() == "/tmp/acme"
    assert "ACTIVE CUSTOMER" in context.prompt() and "/tmp/acme" in context.prompt()
    context.session_set("sess-123")
    assert context.session_get() == "sess-123"
    context.switch("Beta LLC")                       # different customer...
    assert context.session_get() != "sess-123"       # ...separate conversation thread


def test_capture_dedup():
    context.switch("Acme")
    data = {"summary": "x", "todos": [], "knowledge": [], "customers": [],
            "tasks": [{"title": "Call Dana", "due": None, "project": None,
                       "customer": "Acme", "priority": "high"}]}
    store.save(data)
    store.save(data)                                  # same item again
    tasks = (context.workspace() / "tasks.md").read_text()
    assert tasks.count("Call Dana") == 1              # deduped by block-id
