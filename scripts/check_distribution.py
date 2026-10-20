"""Fail closed on accidental private-source, history or credential export."""
import json
import re
import base64
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = frozenset({
    ".gitignore", ".claude-plugin/marketplace.json", "LICENSE", "README.md",
    ".github/workflows/verify.yml", ".github/workflows/publish-registry.yml",
    "plugins/daknode/.claude-plugin/plugin.json", "plugins/daknode/.mcp.json",
    "plugins/daknode/skills/email/SKILL.md", "registry/server.json",
    "scripts/check_distribution.py", "scripts/check_pypi.py",
    "examples/python/requirements.txt", "examples/python/requirements-langchain.txt",
    "examples/python/requirements-google-adk.txt", "examples/python/requirements-livekit.txt",
    "examples/python/daknode_tools.py", "examples/python/langchain_example.py",
    "examples/python/google_adk_example.py", "examples/python/livekit_example.py",
    "examples/python/test_examples.py", "examples/typescript/package.json",
    "examples/typescript/package-lock.json", "examples/typescript/tsconfig.json",
    "examples/typescript/read-inbox.ts", "examples/typescript/test.mjs",
    ".agents/plugins/marketplace.json", "cursor/install.md",
    "plugins/daknode-codex/.codex-plugin/plugin.json", "plugins/daknode-codex/.mcp.json",
    "plugins/daknode-codex/skills/daknode-email/SKILL.md",
    "skills/daknode-email/SKILL.md", "scripts/build_platforms.py",
    "examples/python/openai_agents_example.py", "examples/python/requirements-openai-agents.txt",
    "examples/typescript/vercel-ai.ts",
})
IGNORED_DIRS = {".git", "node_modules", "dist", ".venv", "__pycache__", ".pytest_cache"}


def check():
    actual = set()
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        assert not path.is_symlink(), f"Symlink refused: {relative}"
        if not path.is_file():
            continue
        name = relative.as_posix()
        assert name in PUBLIC_FILES, f"Unapproved export file: {name}"
        actual.add(name)
        content = path.read_text()
        assert not re.search(r"(?:dak_(?:live|test)_|whsec_|sk_live_)[A-Za-z0-9]{12,}", content), f"Credential-shaped value in {name}"
        assert ("-----BEGIN " + "PRIVATE KEY-----") not in content, f"Private key in {name}"
    assert actual == PUBLIC_FILES, f"Missing public files: {sorted(PUBLIC_FILES - actual)}"
    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    assert marketplace["name"] == "daknode"
    assert marketplace["plugins"][0]["source"] == "./plugins/daknode"
    plugin = json.loads((ROOT / "plugins/daknode/.claude-plugin/plugin.json").read_text())
    assert plugin["license"] == "MIT" and plugin["name"] == "daknode"
    assert not set(plugin) & {"hooks", "agents", "permissions"}
    config = json.loads((ROOT / "plugins/daknode/.mcp.json").read_text())
    assert config == {"daknode": {"command": "uvx", "args": ["--from", "daknode-mcp==0.3.2", "daknode-mcp"], "env": {"DAKNODE_API_KEY": "${DAKNODE_API_KEY:-}"}}}
    server = json.loads((ROOT / "registry/server.json").read_text())
    assert server["name"] == "io.github.Subodh103/daknode"
    assert server["version"] == "0.3.2"
    assert len(server["description"]) <= 100
    package = server["packages"][0]
    assert package["identifier"] == "daknode-mcp" and package["version"] == "0.3.2"
    assert package["transport"] == {"type": "stdio"}
    assert package["environmentVariables"][0]["isSecret"] is True
    canonical = (ROOT / "skills/daknode-email/SKILL.md").read_bytes()
    assert (ROOT / "plugins/daknode/skills/email/SKILL.md").read_bytes() == canonical
    assert (ROOT / "plugins/daknode-codex/skills/daknode-email/SKILL.md").read_bytes() == canonical
    portable = json.loads((ROOT / "plugins/daknode-codex/.codex-plugin/plugin.json").read_text())
    assert portable["requires_local_executor"] is True
    assert portable["mcpServers"] == "./.mcp.json" and portable["skills"] == "./skills/"
    assert not set(portable) & {"hooks", "permissions", "agents"}
    catalog = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text())
    assert catalog["plugins"][0]["source"] == {"source": "local", "path": "./plugins/daknode-codex"}
    launch = {"command": "uvx", "args": ["--from", "daknode-mcp==0.3.2", "daknode-mcp"]}
    mcp = json.loads((ROOT / "plugins/daknode-codex/.mcp.json").read_text())
    assert mcp["mcpServers"] == {"daknode": {"type": "stdio", **launch, "env_vars": ["DAKNODE_API_KEY"]}}
    cursor = re.search(r"\[Add DakNode MCP\]\((cursor://[^\s)]+)\)", (ROOT / "cursor/install.md").read_text())
    assert cursor, "Missing Cursor install link"
    parsed = urlparse(cursor.group(1))
    assert parsed.netloc == "anysphere.cursor-deeplink" and parsed.path == "/mcp/install"
    query = parse_qs(parsed.query)
    assert query["name"] == ["daknode"]
    assert json.loads(base64.b64decode(query["config"][0], validate=True)) == launch
    assert "Permission is hereby granted" in (ROOT / "LICENSE").read_text()
    print(f"Distribution boundary and manifests passed: {len(actual)} allowlisted files")


if __name__ == "__main__":
    check()
