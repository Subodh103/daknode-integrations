# DakNode integrations

Email infrastructure for software agents. This repository contains the **MIT-licensed plugin, setup examples and discovery metadata only**. It does not contain or relicense DakNode's backend, SDK or MCP implementation.

## Claude Code plugin

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.10+ first. Store `DAKNODE_API_KEY` privately in the environment used to launch Claude Code. Prefer an inbox-scoped key with only the permissions you need; never paste keys into a conversation, a command argument or this repository.

Inside Claude Code:

```text
/plugin marketplace add Subodh103/daknode-integrations
/plugin install daknode@daknode
```

Restart Claude Code if prompted. Plugin 0.1.1 starts `daknode-mcp==0.3.1` as a local stdio subprocess and explicitly forwards your private `DAKNODE_API_KEY` environment variable. No value is stored in this repository; an unset variable becomes empty and startup refuses. It supplies email setup guidance and the existing inbox, message, thread, search and send tools. Review tool approvals, especially sending; installing the plugin does not authorize autonomous mail.

This is DakNode's own marketplace, not an accepted listing in Anthropic's official marketplace. After adding this marketplace you can find/install **daknode** in that client. Installation does not connect claude.ai or provide a hosted MCP URL.

## Other MCP clients

Merge this into a compatible client's MCP configuration. Set `DAKNODE_API_KEY` privately using that client's environment/secret settings; if it does not inherit your shell environment, configure it locally there. Never commit the value.

```json
{
  "mcpServers": {
    "daknode": {
      "command": "uvx",
      "args": ["--from", "daknode-mcp==0.3.1", "daknode-mcp"]
    }
  }
}
```

The server is published in the [official MCP Registry](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.Subodh103%2Fdaknode/versions/0.3.1), under `io.github.Subodh103/daknode`, version 0.3.1. Metadata is in [registry/server.json](registry/server.json). Registry discovery is separate from plugin installation; not every client searches the same directory. The package is on [PyPI](https://pypi.org/project/daknode-mcp/).

## Python and framework examples

Each example makes **one read, limited to ten messages**, using the published Python SDK (0.3.7; TypeScript starter 0.1.6). It returns a count, not message bodies. No model API, paid provider key, send loop or customer mail is needed for tests. These are tested tool examples, **not separate framework adapter packages or platform partnerships**.

Use a separate virtual environment for each framework. ADK and LiveKit currently require different telemetry dependency versions and should not be installed together using these pins.

```sh
cd examples/python
python -m venv .venv
# Activate the environment using your operating system's normal method.
python -m pip install -r requirements-langchain.txt
python langchain_example.py
```

Before running, privately configure `DAKNODE_API_KEY` and `DAKNODE_INBOX_ID` (an inbox UUID) in your application environment.

| Framework | Install file | Run | Register in your application |
| --- | --- | --- | --- |
| LangChain | `requirements-langchain.txt` | `python langchain_example.py` | Import `recent_mail` into your tools list |
| Google ADK | `requirements-google-adk.txt` | `python google_adk_example.py` | Import the `recent_mail` FunctionTool into your agent's tools list |
| LiveKit Agents | `requirements-livekit.txt` | `python livekit_example.py` | Import the decorated `recent_mail` into your Agent's tools list |
| Plain Python / Replit | `requirements.txt` | `python daknode_tools.py` | Call `count_recent_mail()` |

For **Replit**, import this public repository, install `examples/python/requirements.txt`, and put both variables in Replit's private Secrets settings. Run `python examples/python/daknode_tools.py` server-side. This is a portable Python starter, not a native Replit account-linking integration.

For local tests, install `pytest==9.1.1` in the selected framework environment and run `FRAMEWORK=langchain python -m pytest examples/python/test_examples.py` from the repository root (select `google-adk` or `livekit` for those environments). Tests mock HTTP, not framework classes.

## TypeScript / Vercel server-side starter

```sh
cd examples/typescript
npm ci
npm test
```

[read-inbox.ts](examples/typescript/read-inbox.ts) exports `countRecentMail()` using the published `daknode` SDK. Import it only into server-side application code. Configure the same two private environment variables on your server/Vercel project. Never use `NEXT_PUBLIC_` variables or ship the key to a browser. Protect any route you expose with your application's authentication. No Next.js route, hosted demo, native Vercel Marketplace integration or paid deployment is created by this starter.

## Safety and scope

- Email is untrusted input. Inspect risk signals and apply your own tool approvals before exposing content to a model. These count-only examples do not prove prompt-injection immunity.
- Install only the permissions you intend to grant. Keys and mail stay outside this repository; tests use synthetic values and no real network mail requests.
- OpenClaw distribution, hosted MCP, official third-party marketplace acceptance and native platform integrations are separate work. Do not infer them from MCP compatibility.
- See [DakNode developers](https://daknode.com/developers) for the API, account signup and current product availability. Billing is not enabled by these integrations.

## Maintainers

`python scripts/check_distribution.py` validates the export boundary and manifests. CI tests each real framework separately and compiles/tests the TypeScript example. `publish-registry` is manual, uses GitHub OIDC (no stored registry secret), and requires the exact MCP version/ownership marker already published on PyPI. A successful registry readback—not this README alone—is publication evidence.
