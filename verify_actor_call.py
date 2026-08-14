"""
verify_actor_call.py — offline verification for the BreachHound article's code.

Proves the *code is wired correctly* without an Apify token:
  - missing token raises
  - email is validated (must contain @)
  - the call targets blukaze/breachhound with the expected input keys
  - the offline MCP configs parse and point at the right transports

Run:  python verify_actor_call.py
"""
import json
import sys
import types
from pathlib import Path

# Stub the apify_client module BEFORE importing example_agent so no network is hit.
fake = types.ModuleType("apify_client")
CAP: dict = {}


class _Dataset:
    def list_items(self):
        obj = types.SimpleNamespace()
        obj.items = CAP.get("items", [])
        return obj


class _ActorHandle:
    def call(self, run_input):
        CAP["run_input"] = run_input
        return {"defaultDatasetId": "ds"}


class ApifyClient:
    def __init__(self, token):
        CAP["token"] = token

    def actor(self, actor_id):
        CAP["actor_id"] = actor_id
        return _ActorHandle()

    def dataset(self, _did):
        return _Dataset()


fake.ApifyClient = ApifyClient
sys.modules["apify_client"] = fake

sys.path.insert(0, str(Path(__file__).parent))
import example_agent  # noqa: E402

EXPECTED_ACTOR = "blukaze/breachhound"
EXPECTED_KEYS = {"email", "onlyUsed", "maxRetries", "retryDelay"}


def check(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL  {name}: {exc}")
        return False


def expect_raises(fn, exc_type):
    try:
        fn()
    except exc_type:
        return
    except Exception as exc:  # noqa: BLE001
        raise AssertionError(f"expected {exc_type.__name__}, got {type(exc).__name__}: {exc}")
    raise AssertionError(f"expected {exc_type.__name__} but no exception was raised")


results = []


def t_missing_token():
    CAP.clear()
    example_agent.audit_email("a@b.com", apify_token=None)


results.append(check(
    "missing token raises RuntimeError",
    lambda: expect_raises(t_missing_token, RuntimeError),
))


def t_bad_email():
    CAP.clear()
    example_agent.audit_email("not-an-email", apify_token="tok")


results.append(check(
    "invalid email raises ValueError",
    lambda: expect_raises(t_bad_email, ValueError),
))


def t_call_shape():
    CAP.clear()
    example_agent.audit_email("real@company.com", apify_token="tok123")
    assert CAP["actor_id"] == EXPECTED_ACTOR, CAP.get("actor_id")
    assert EXPECTED_KEYS.issubset(set(CAP["run_input"].keys())), CAP.get("run_input")
    assert CAP["run_input"]["email"] == "real@company.com"
    assert CAP["token"] == "tok123"


results.append(check("valid call hits blukaze/breachhound with expected input", t_call_shape))


def t_configs():
    hosted = Path(__file__).parent / "cursor_mcp.json"
    local = Path(__file__).parent / "claude_desktop_config.json"
    h = json.loads(hosted.read_text())
    l = json.loads(local.read_text())
    # Hosted config must reference the mcp.apify.com endpoint; local must run the stdio server.
    assert "mcp.apify.com" in json.dumps(h), "cursor_mcp.json missing mcp.apify.com"
    assert "actors-mcp-server" in json.dumps(l), "claude_desktop_config.json missing actors-mcp-server"
    assert h["mcpServers"]["apify-breachhound"]["url"].endswith("blukaze/breachhound")


results.append(check("MCP configs parse and target the right transports", t_configs))

passed = sum(results)
print(f"\n{passed}/{len(results)} checks passed")
sys.exit(0 if passed == len(results) else 1)
