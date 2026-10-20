"""Generate platform packages from one skill and MCP pin; --check never writes."""
import argparse
import base64
import json
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
MCP_VERSION = "0.3.2"


def artifacts():
    skill = (ROOT / "skills/daknode-email/SKILL.md").read_text()
    launch = {"command": "uvx", "args": ["--from", f"daknode-mcp=={MCP_VERSION}", "daknode-mcp"]}
    config = base64.b64encode(json.dumps(launch, separators=(",", ":")).encode()).decode()
    link = "cursor://anysphere.cursor-deeplink/mcp/install?" + urlencode({"name": "daknode", "config": config})
    return {
        "plugins/daknode/skills/email/SKILL.md": skill,
        "plugins/daknode-codex/skills/daknode-email/SKILL.md": skill,
        "plugins/daknode-codex/.codex-plugin/plugin.json": json.dumps({
            "name": "daknode", "version": "0.2.0",
            "description": "Local DakNode email tools and user-directed email workflows.",
            "license": "MIT", "homepage": "https://daknode.com/developers",
            "repository": "https://github.com/Subodh103/daknode-integrations",
            "requires_local_executor": True, "skills": "./skills/", "mcpServers": "./.mcp.json",
            "interface": {"displayName": "DakNode", "shortDescription": "Email tools for software agents",
                "developerName": "DakNode", "category": "Productivity", "capabilities": ["Read", "Write"]},
        }, indent=2) + "\n",
        "plugins/daknode-codex/.mcp.json": json.dumps({
            "mcpServers": {"daknode": {"type": "stdio", **launch, "env_vars": ["DAKNODE_API_KEY"]}},
        }, indent=2) + "\n",
        ".agents/plugins/marketplace.json": json.dumps({"name": "daknode-local",
            "interface": {"displayName": "DakNode local integrations"}, "plugins": [{
                "name": "daknode", "source": {"source": "local", "path": "./plugins/daknode-codex"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Productivity"}]}, indent=2) + "\n",
        "cursor/install.md": "# Add DakNode to Cursor\n\n[Add DakNode MCP](" + link + ")\n\n"
            "Requires uv and Python 3.10+. Review Cursor's installation prompt. "
            "The link contains configuration only, never credentials. Set DAKNODE_API_KEY "
            "privately in Cursor's MCP environment/secret settings before connecting; "
            "shell inheritance depends on how Cursor was launched. Never commit that value.\n\n"
            "For workflow guidance, install skills/daknode-email from this repository "
            "using your client's skill installer. Installation does not authorize sending. "
            "This is a local subprocess, not a hosted MCP service or Cursor Marketplace listing.\n",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for relative, content in artifacts().items():
        path = ROOT / relative
        if args.check:
            assert path.is_file() and path.read_text() == content, f"Regenerate platform artifact: {relative}"
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    print("Platform packages match the canonical skill and MCP version")


if __name__ == "__main__":
    main()
