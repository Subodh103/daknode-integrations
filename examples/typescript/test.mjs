import { test } from "node:test";
import assert from "node:assert/strict";
import { countRecentMail } from "./dist/read-inbox.js";
import { daknodeTools } from "./dist/vercel-ai.js";

test("server starter uses the published SDK, bounded read and private key", async () => {
  process.env.DAKNODE_API_KEY = "example-test-value-not-a-real-key";
  process.env.DAKNODE_INBOX_ID = "11111111-1111-4111-8111-111111111111";
  const original = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async request => {
    calls++;
    assert.equal(request.method, "GET");
    assert.equal(new URL(request.url).searchParams.get("limit"), "10");
    assert.equal(request.headers.get("Authorization"), "Bearer example-test-value-not-a-real-key");
    assert.match(new URL(request.url).pathname, /inboxes\/11111111-1111-4111-8111-111111111111\/messages$/);
    return Response.json({ items: [{ id: "fixture" }], has_more: false });
  };
  try {
    assert.equal(await countRecentMail(), 1);
    assert.equal(calls, 1);
    assert.deepEqual(await daknodeTools.count_recent_mail.execute({}, {
      toolCallId: "test-only", messages: [] }), { count: 1 });
    assert.equal(calls, 2);
    globalThis.fetch = async () => Response.json({ error: { message: "private-context" } }, { status: 403 });
    await assert.rejects(countRecentMail, /^Error: DakNode refused the read$/);
    await assert.rejects(() => daknodeTools.count_recent_mail.execute({}, {
      toolCallId: "test-only", messages: [] }), /^Error: DakNode refused the read$/);
    delete process.env.DAKNODE_API_KEY;
    await assert.rejects(countRecentMail, /Configure the private server environment/);
  } finally {
    globalThis.fetch = original;
    delete process.env.DAKNODE_API_KEY;
    delete process.env.DAKNODE_INBOX_ID;
  }
});
