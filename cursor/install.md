# Add DakNode to Cursor

[Add DakNode MCP](cursor://anysphere.cursor-deeplink/mcp/install?name=daknode&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJkYWtub2RlLW1jcD09MC4zLjIiLCJkYWtub2RlLW1jcCJdfQ%3D%3D)

Requires uv and Python 3.10+. Review Cursor's installation prompt. The link contains configuration only, never credentials. Set DAKNODE_API_KEY privately in Cursor's MCP environment/secret settings before connecting; shell inheritance depends on how Cursor was launched. Never commit that value.

For workflow guidance, install skills/daknode-email from this repository using your client's skill installer. Installation does not authorize sending. This is a local subprocess, not a hosted MCP service or Cursor Marketplace listing.
