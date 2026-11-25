import { tool } from "ai";
import { DakNodeToolkit, type ToolkitOptions } from "./index.js";

/** Register these tools in the customer's agent. Does not create an agent/model. */
export function createVercelTools(options: ToolkitOptions) {
  const toolkit = new DakNodeToolkit(options);
  return Object.fromEntries(toolkit.definitions().map(definition => [
    `daknode_${definition.name}`,
    tool({ description: definition.description, inputSchema: definition.inputSchema, execute: (input, context) => {
      if (!context.abortSignal) return definition.execute(input);
      const signal = options.signal ? AbortSignal.any([options.signal, context.abortSignal]) : context.abortSignal;
      return new DakNodeToolkit({ ...options, signal }).execute(definition.name, input);
    } }),
  ]));
}
