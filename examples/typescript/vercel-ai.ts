/** Customer-side, server-only tool. No model call or send loop on import. */
import { tool } from "ai";
import { z } from "zod";
import { countRecentMail } from "./read-inbox.js";

export const daknodeTools = {
  count_recent_mail: tool({
    description: "Count up to ten retained messages in the server-configured DakNode inbox. No message content is returned.",
    inputSchema: z.object({}),
    execute: async () => ({ count: await countRecentMail() }),
  }),
};
