import json
import os
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from daknode_toolkit import DakNodeToolkit, ToolkitRefused

INBOX = "11111111-1111-4111-8111-111111111111"
OTHER = "22222222-2222-4222-8222-222222222222"


def toolkit(handler=None, **kwargs):
    requests = []

    def reply(request):
        requests.append(request)
        if handler:
            value = handler(request)
            if value is not None:
                return value
        if request.url.path == "/v1/mcp/identity":
            return httpx.Response(200, json={"inbox_id": INBOX})
        if (
            request.url.path
            in (f"/v1/messages/{INBOX}", f"/v1/threads/{INBOX}", f"/v1/drafts/{INBOX}")
            and request.method == "GET"
        ):
            return httpx.Response(200, json={"id": INBOX, "inbox_id": INBOX})
        return httpx.Response(
            200, json={"items": [], "has_more": False, "next_cursor": None}
        )

    return DakNodeToolkit(
        api_key="synthetic-never-live",
        inbox_id=INBOX,
        _transport=httpx.MockTransport(reply),
        **kwargs,
    ), requests


def test_default_reads_only_and_no_request_on_construction():
    t, requests = toolkit()
    assert len(t.functions()) == 6 and requests == []
    with pytest.raises(ToolkitRefused):
        t.create_draft("a@example.test", "s", "b")
    assert requests == []
    t.close()


def test_scoped_identity_refusal_precedes_data():
    t, requests = toolkit(lambda r: httpx.Response(200, json={"inbox_id": OTHER}))
    with pytest.raises(ToolkitRefused):
        t.list_messages()
    assert len(requests) == 1


@pytest.mark.parametrize(
    "name,args",
    [
        ("list_messages", ()),
        ("list_threads", ()),
        ("get_message", (INBOX,)),
        ("get_thread", (INBOX,)),
        ("list_drafts", ()),
        ("search", ("query",)),
    ],
)
def test_reads_use_existing_sdk_transport_and_auth(name, args):
    t, requests = toolkit()
    getattr(t, name)(*args)
    assert all(
        r.headers["authorization"] == "Bearer synthetic-never-live" for r in requests
    )
    assert requests[0].url.path == "/v1/mcp/identity"
    assert len(requests) == 2
    t.close()


def test_draft_never_disables_human_approval():
    t, requests = toolkit(writes={"create_draft", "update_draft", "cancel_draft"})
    t.create_draft("a@example.test", "subject", "untrusted email")
    body = json.loads(requests[-1].content)
    assert (
        body["require_human_approval"] is True and body["message"]["inbox_id"] == INBOX
    )
    t.update_draft(INBOX, OTHER, "a@example.test", "changed", "b")
    assert json.loads(requests[-1].content)["require_human_approval"] is True
    t.cancel_draft(INBOX, OTHER)
    assert requests[-1].url.path.endswith("/cancel")


def test_review_policy_rejects_direct_send_and_unknown_capabilities():
    for kwargs in [
        {"writes": {"send"}},
        {"writes": {"approve_draft"}},
        {"writes": {"create_inbox"}},
    ]:
        with pytest.raises(ValueError):
            toolkit(**kwargs)


def test_direct_send_has_stable_idempotency_and_no_retry():
    t, requests = toolkit(writes={"send"}, sending_policy="direct")
    t.send("a@example.test", "s", "b", "request-once", INBOX)
    assert requests[-1].headers["idempotency-key"] == "request-once"
    assert sum(r.url.path == "/v1/send" for r in requests) == 1


def test_cross_inbox_resource_is_not_returned_or_mutated():
    def response(r):
        if r.url.path == f"/v1/drafts/{INBOX}":
            return httpx.Response(200, json={"inbox_id": OTHER})

    t, requests = toolkit(response, writes={"cancel_draft"})
    with pytest.raises(ToolkitRefused):
        t.cancel_draft(INBOX, OTHER)
    assert all(not r.url.path.endswith("/cancel") for r in requests)


def test_truncated_output_and_generic_failures():
    def response(r):
        if r.url.path.endswith("/messages"):
            return httpx.Response(200, json={"items": [{"text": "x" * 5000}]})

    t, _ = toolkit(response)
    assert t.list_messages()["items"][0]["text"].endswith("[truncated]")
    t, _ = toolkit(
        lambda r: httpx.Response(403, json={"private": "synthetic-never-live"})
    )
    with pytest.raises(ToolkitRefused) as exc:
        t.list_messages()
    assert "synthetic-never-live" not in str(exc.value)


@pytest.mark.parametrize(
    "framework",
    [os.environ["TOOLKIT_FRAMEWORK"]]
    if os.environ.get("TOOLKIT_FRAMEWORK")
    else ["langchain", "crewai", "llamaindex"],
)
def test_real_framework_objects_schema_and_execution(framework, monkeypatch, tmp_path):
    monkeypatch.setenv("OTEL_SDK_DISABLED", "true")
    monkeypatch.setenv("CREWAI_TELEMETRY_DISABLED", "true")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")
    monkeypatch.setenv("CREWAI_STORAGE_DIR", str(tmp_path))
    if framework == "crewai":
        # Isolate the framework's unrelated local login storage, not its tools.
        from crewai_core.token_manager import TokenManager

        auth_path = tmp_path / "framework-auth"
        auth_path.mkdir()
        monkeypatch.setattr(
            TokenManager, "_get_secure_storage_path", staticmethod(lambda: auth_path)
        )
    t, requests = toolkit(writes={"create_draft"})
    tools = getattr(t, framework)()
    assert len(tools) == 7 and requests == []
    if framework == "langchain":
        item = next(x for x in tools if x.name == "daknode_list_messages")
        assert "api_key" not in str(item.args_schema.model_json_schema())
        result = item.invoke({"limit": 2})
    elif framework == "crewai":
        item = next(x for x in tools if x.name == "daknode_list_messages")
        assert "api_key" not in str(item.args_schema.model_json_schema())
        result = item.run(limit=2)
    else:
        item = next(x for x in tools if x.metadata.name == "daknode_list_messages")
        assert "api_key" not in str(item.metadata.get_parameters_dict())
        result = item.call(limit=2).raw_output
    assert result["items"] == [] and len(requests) == 2
    t.close()
