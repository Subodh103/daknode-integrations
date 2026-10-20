/** Server-side only. Import into a server route, never a browser component. */
import { createDakNodeClient } from "daknode";

export async function countRecentMail(): Promise<number> {
  const apiKey = process.env.DAKNODE_API_KEY?.trim();
  const inboxId = process.env.DAKNODE_INBOX_ID;
  if (!apiKey || !inboxId) throw new Error("Configure the private server environment");
  const client = createDakNodeClient({ apiKey });
  let result;
  try { result = await client.messages.list(inboxId, { limit: 10 }); }
  catch { throw new Error("DakNode could not be reached; no mail was changed"); }
  if (!result.response.ok || !result.data) throw new Error("DakNode refused the read");
  return result.data.items.length;
}
