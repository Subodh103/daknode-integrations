"""Fail closed on accidental private-source, history or credential export."""
import json
import re
from pathlib import Path

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
    assert config == {"daknode": {"command": "uvx", "args": ["--from", "daknode-mcp==0.3.1", "daknode-mcp"], "env": {"DAKNODE_API_KEY": "${DAKNODE_API_KEY:-}"}}}
    server = json.loads((ROOT / "registry/server.json").read_text())
    assert server["name"] == "io.github.Subodh103/daknode"
    assert server["version"] == "0.3.1"
    assert len(server["description"]) <= 100
    package = server["packages"][0]
    assert package["identifier"] == "daknode-mcp" and package["version"] == "0.3.1"
    assert package["transport"] == {"type": "stdio"}
    assert package["environmentVariables"][0]["isSecret"] is True
    assert "Permission is hereby granted" in (ROOT / "LICENSE").read_text()
    print(f"Distribution boundary and manifests passed: {len(actual)} allowlisted files")


if __name__ == "__main__":
    check()
