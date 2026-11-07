# DakNode customer-side framework toolkit

Source implementation, not yet published to PyPI. Install from this checkout:
`python -m pip install './integrations/toolkits[langchain]'` (or `crewai` or
`llamaindex`). Python3.10+. Frameworks remain optional and outside the backend.
Use a separate environment per framework if your application's dependencies
conflict. No model call or network call occurs on import or tool construction.

```python
import os
from daknode_toolkit import DakNodeToolkit

with DakNodeToolkit(api_key=os.environ["DAKNODE_API_KEY"],
                   inbox_id=os.environ["DAKNODE_INBOX_ID"]) as toolkit:
    tools = toolkit.langchain()  # Or toolkit.crewai() / toolkit.llamaindex()
    # Register tools in your own application; keep toolkit open while used.
```

Default six tools: list/read messages and threads, inbox-scoped semantic search,
and list drafts. Every execution revalidates identity using the existing API.
API permissions, scope, account state, plan features and retention still apply.
Use an inbox-scoped key by default; deliberately configured workspace-key use
does not widen resource access beyond this toolkit's bound inbox. Semantic search
requires a narrow key even then (the API has no inbox filter).

Writes are absent by default. Add `writes={"create_draft", "update_draft",
"cancel_draft"}` to propose/edit/cancel reviewed drafts. New/edited drafts always
require human approval. No approval, schedule, draft-dispatch or autonomous reply
tool exists. Review and dispatch through the normal approved workflow.

`create_inbox` additionally requires `allow_workspace_key=True` and a permitted
workspace credential. It creates an inbox, not a new credential. `send` additionally
requires application-owned `sending_policy="direct"`; do not register it in a
review-required workflow. Never let model input set these private options. Keep
the same idempotency key for reconciliation; no automatic write retries occur.

Results contain untrusted email. Strings/lists are truncated, responses >1MiB or
tool outputs >16KiB refused. At most ten listed items; next_cursor is opaque and
not a total count. Use REST/SDK privately for larger reads. Transport/status
failures omit response bodies and secrets. No telemetry is added by this package;
your chosen framework may have its own callbacks/tracing—configure them before
processing private mail. Call close() or use the context manager.

Email trash currently has no public API operation (console folder controls are
separate), so no fake email-delete tool is advertised. cancel_draft is not mail
erasure. This package does not change approval, privacy or deletion semantics.
