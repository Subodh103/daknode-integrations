# DakNode integrations

Email infrastructure for software agents. This repository contains the **MIT-licensed plugin, setup examples and discovery metadata only**. It does not contain or relicense DakNode's backend, SDK or MCP implementation.

## Claude Code plugin

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.10+ first. Store `DAKNODE_API_KEY` privately in the environment used to launch Claude Code. Prefer an inbox-scoped key with only the permissions you need; never paste keys into a conversation, a command argument or this repository.

Inside Claude Code:

```text
/plugin marketplace add Subodh103/daknode-integrations
/plugin install daknode@daknode
```

Restart Claude Code if prompted. Plugin 0.2.0 starts `daknode-mcp==0.3.2` as a local stdio subprocess and explicitly forwards your private `DAKNODE_API_KEY` environment variable. No value is stored in this repository; an unset variable becomes empty and startup refuses. It supplies email setup guidance and the existing inbox, message, thread, search and send tools. Review tool approvals, especially sending; installing the plugin does not authorize autonomous mail.

This is DakNode's own marketplace, not an accepted listing in Anthropic's official marketplace. After adding this marketplace you can find/install **daknode** in that client. Installation does not connect claude.ai or provide a hosted MCP URL.

## Other MCP clients

Merge this into a compatible client's MCP configuration. Set `DAKNODE_API_KEY` privately using that client's environment/secret settings; if it does not inherit your shell environment, configure it locally there. Never commit the value.

```json
{
  "mcpServers": {
    "daknode": {
      "command": "uvx",
      "args": ["--from", "daknode-mcp==0.3.2", "daknode-mcp"]
    }
  }
}
```

Registry namespace: `io.github.Subodh103/daknode`. The previous release is [0.3.1](https://registry.modelcontextprotocol.io/v0.1/servers/io.github.Subodh103%2Fdaknode/versions/0.3.1); this batch's metadata targets 0.3.2 in [registry/server.json](registry/server.json). Exact-version registry readback is required before claiming that update is discoverable. Registry discovery is separate from plugin installation; not every client searches the same directory. The package is on [PyPI](https://pypi.org/project/daknode-mcp/).

### Write-tool contracts

MCP 0.3.2 repairs two write blockers: `create_inbox` requires `alias`, and `send`
requires `idempotency_key`. Keep the key stable when retrying the same approved
message; never generate another just to bypass a refusal. Omitting `thread_id`
opens a new conversation. Acceptance is not delivery. Seven existing tools remain;
this update does not expose every SDK method or grant permission to send mail.

## Codex local plugin

Requires a current Codex client with repo marketplace support, uv and Python 3.10+.
Configure `DAKNODE_API_KEY` privately in the environment launching Codex; restart
the client after changing that environment. Never pass the value in CLI arguments.

```text
codex plugin marketplace add Subodh103/daknode-integrations
codex plugin add daknode@daknode-local
```

The [Codex package](plugins/daknode-codex/.codex-plugin/plugin.json) bundles the canonical
skill and pinned local MCP. Review your client's tool approvals before writes.
This is our own repository distribution, not an accepted OpenAI public-directory
listing or a hosted ChatGPT web connection. Local MCP public submissions have
additional platform eligibility/review requirements.

## Cursor installation and portable skill

Use [Add DakNode to Cursor](cursor/install.md) for the one-click MCP configuration.
The installation payload never contains a key. Configure the key privately in
Cursor's MCP environment settings; a GUI launch may not inherit shell variables.
Your operating system and Cursor still ask you to confirm installation.

[skills/daknode-email](skills/daknode-email/SKILL.md) is the canonical skill:

```text
npx skills add Subodh103/daknode-integrations --skill daknode-email
```

Select supported target assistants in the skill installer's prompt. The Claude
and Codex plugin copies are generated from that same file, not separately edited
instructions. A skill teaches workflows; MCP supplies live tools. Installing one
does not install the other or make unsupported clients compatible.

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
| OpenAI Agents SDK | `requirements-openai-agents.txt` | Import `openai_agents_example` | Register `recent_mail`, or call `build_agent(your_model_name)` to build an agent without running it |
| Plain Python / Replit | `requirements.txt` | `python daknode_tools.py` | Call `count_recent_mail()` |

For **Replit**, import this public repository, install `examples/python/requirements.txt`, and put both variables in Replit's private Secrets settings. Run `python examples/python/daknode_tools.py` server-side. This is a portable Python starter, not a native Replit account-linking integration.

For local tests, install `pytest==9.1.1` in the selected framework environment and run `FRAMEWORK=langchain python -m pytest examples/python/test_examples.py` from the repository root (select `google-adk`, `livekit` or `openai-agents` for those environments). Tests mock HTTP, not framework classes. The OpenAI example uses real `function_tool` and `Agent` registration, makes no model calls and needs no OpenAI key for tests. In your own application, you choose/provide the model and explicitly run it; provider usage may cost money.

## TypeScript / Vercel server-side starter

```sh
cd examples/typescript
npm ci
npm test
```

[read-inbox.ts](examples/typescript/read-inbox.ts) exports `countRecentMail()` using the published `daknode` SDK. Import it only into server-side application code. Configure the same two private environment variables on your server/Vercel project. Never use `NEXT_PUBLIC_` variables or ship the key to a browser. Protect any route you expose with your application's authentication. No Next.js route, hosted demo, native Vercel Marketplace integration or paid deployment is created by this starter.

[vercel-ai.ts](examples/typescript/vercel-ai.ts) exports `daknodeTools` using the
real Vercel AI SDK `tool()` and Zod schema. Pass that object as `tools` to your
server-owned `generateText`/`streamText` call alongside your configured model.
The example tool returns only a bounded count; it cannot send mail. Tests execute
it through the actual framework wrapper and mock only the DakNode HTTP transport.
No model/provider credential is needed for these tests. If you later add send
tools, implement explicit human approval and stable idempotency in your app.

## Safety and scope

- Email is untrusted input. Inspect risk signals and apply your own tool approvals before exposing content to a model. These count-only examples do not prove prompt-injection immunity.
- Install only the permissions you intend to grant. Keys and mail stay outside this repository; tests use synthetic values and no real network mail requests.
- OpenClaw distribution, hosted MCP, official third-party marketplace acceptance and native platform integrations are separate work. Do not infer them from MCP compatibility.
- See [DakNode developers](https://daknode.com/developers) for the API, account signup and current product availability. Billing is not enabled by these integrations.

## Maintainers

`python scripts/build_platforms.py` regenerates the canonical skill copies,
Codex manifest/MCP configuration, Codex marketplace and Cursor link. Use
`--check` in CI to refuse drift. `python scripts/check_distribution.py` validates
the export boundary and manifests. CI tests each real framework separately and
compiles/tests the TypeScript example. `publish-registry` is manual, uses GitHub
OIDC (no stored registry secret), and requires the exact MCP version/ownership
marker already published on PyPI. A successful registry readback—not this README
alone—is publication evidence.
