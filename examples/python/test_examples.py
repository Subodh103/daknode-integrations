"""Real SDK/framework wrappers; only the HTTP transport is replaced."""
import asyncio
import os

import httpx
import pytest
from daknode import AuthenticatedClient

import daknode_tools


@pytest.fixture
def transport(monkeypatch):
    monkeypatch.setenv("DAKNODE_API_KEY", "example-test-value-not-a-real-key")
    monkeypatch.setenv("DAKNODE_INBOX_ID", "11111111-1111-4111-8111-111111111111")
    calls = []

    def handle(request):
        calls.append(request)
        assert request.method == "GET"
        assert request.url.host == "api.daknode.com"
        assert request.url.path.endswith("/inboxes/11111111-1111-4111-8111-111111111111/messages")
        assert request.url.params["limit"] == "10"
        assert request.headers["authorization"] == "Bearer example-test-value-not-a-real-key"
        return httpx.Response(200, json={"items": [], "has_more": False, "next_cursor": None})

    def client(**kwargs):
        return AuthenticatedClient(**kwargs, httpx_args={"transport": httpx.MockTransport(handle)})

    monkeypatch.setattr(daknode_tools, "AuthenticatedClient", client)
    return calls


def test_shared_sdk_bounded_read(transport):
    assert daknode_tools.count_recent_mail() == 0
    assert len(transport) == 1


@pytest.mark.parametrize("field,value", [("DAKNODE_API_KEY", ""), ("DAKNODE_INBOX_ID", ""), ("DAKNODE_INBOX_ID", "not-a-uuid")])
def test_configuration_refused_before_http(transport, monkeypatch, field, value):
    monkeypatch.setenv(field, value)
    with pytest.raises(RuntimeError):
        daknode_tools.count_recent_mail()
    assert not transport


def test_transport_errors_do_not_expose_private_context(transport, monkeypatch):
    def fail(**kwargs):
        raise RuntimeError("private-request-context")
    monkeypatch.setattr(daknode_tools, "AuthenticatedClient", fail)
    with pytest.raises(RuntimeError, match="could not be reached") as error:
        daknode_tools.count_recent_mail()
    assert "private-request-context" not in str(error.value)
    assert error.value.__suppress_context__


def test_http_refusal_does_not_echo_response(transport, monkeypatch):
    def refuse(request):
        return httpx.Response(403, json={"detail": "private-response-context"})
    monkeypatch.setattr(daknode_tools, "AuthenticatedClient", lambda **kwargs: AuthenticatedClient(
        **kwargs, httpx_args={"transport": httpx.MockTransport(refuse)}))
    with pytest.raises(RuntimeError, match="refused the read") as error:
        daknode_tools.count_recent_mail()
    assert "private-response-context" not in str(error.value)


def test_real_selected_framework_tool(transport):
    framework = os.environ.get("FRAMEWORK")
    if framework == "langchain":
        from langchain_example import recent_mail
        assert recent_mail.name == "daknode_count_recent_mail"
        assert recent_mail.invoke({}) == 0
    elif framework == "google-adk":
        from google_adk_example import recent_mail
        assert recent_mail.name == "count_recent_mail"
        assert asyncio.run(recent_mail.run_async(args={}, tool_context=None)) == 0
    elif framework == "livekit":
        from livekit_example import recent_mail
        assert recent_mail() == 0
    elif framework == "openai-agents":
        from agents.tool_context import ToolContext
        from openai_agents_example import recent_mail, build_agent
        assert recent_mail.name == "count_recent_mail"
        context = ToolContext(context=None, tool_name=recent_mail.name,
            tool_call_id="test-only", tool_arguments="{}")
        assert asyncio.run(recent_mail.on_invoke_tool(context, "{}")) == 0
        agent = build_agent("customer-selected-model")
        assert agent.tools == [recent_mail]
    else:
        pytest.fail("Set FRAMEWORK to langchain, google-adk, livekit or openai-agents; no silent skips")
    assert len(transport) == 1
