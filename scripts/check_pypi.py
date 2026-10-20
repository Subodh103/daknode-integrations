"""Verify the exact public PyPI release owns this registry name."""
import json
from urllib.request import urlopen

from check_distribution import ROOT

server = json.loads((ROOT / "registry/server.json").read_text())
package = server["packages"][0]
url = f"https://pypi.org/pypi/{package['identifier']}/{package['version']}/json"
with urlopen(url, timeout=30) as response:
    release = json.load(response)
assert release["info"]["version"] == package["version"]
assert f"mcp-name: {server['name']}" in release["info"]["description"]
assert {item["packagetype"] for item in release["urls"]} >= {"bdist_wheel", "sdist"}
print("Exact PyPI release, distributions and MCP ownership marker verified")
