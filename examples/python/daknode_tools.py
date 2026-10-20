"""Customer-side tools: one bounded SDK read, no mail contents or agent loop."""
import os
from uuid import UUID

from daknode import AuthenticatedClient
from daknode.api.messages import list_messages


def count_recent_mail() -> int:
    """Count up to ten retained messages in the privately configured inbox."""
    key = os.environ.get("DAKNODE_API_KEY", "").strip()
    identifier = os.environ.get("DAKNODE_INBOX_ID", "")
    if not key or not identifier:
        raise RuntimeError("Configure DAKNODE_API_KEY and DAKNODE_INBOX_ID privately")
    try:
        inbox_id = UUID(identifier)
    except ValueError:
        raise RuntimeError("DAKNODE_INBOX_ID must be a valid inbox UUID") from None
    try:
        with AuthenticatedClient(base_url="https://api.daknode.com", token=key, timeout=10) as client:
            response = list_messages.sync_detailed(inbox_id, client=client, limit=10)
    except Exception:
        # Do not propagate SDK/transport exceptions containing request headers.
        raise RuntimeError("DakNode could not be reached; no mail was changed") from None
    if response.status_code != 200 or response.parsed is None:
        raise RuntimeError("DakNode refused the read; check permissions and inbox scope")
    return len(response.parsed.items)


if __name__ == "__main__":
    print(count_recent_mail())
