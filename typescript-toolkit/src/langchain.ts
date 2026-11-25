import { tool } from "@langchain/core/tools";
import { DakNodeToolkit, type ToolkitOptions } from "./index.js";

/** Actual LangChain tools; no model, agent loop or automatic send registration. */
export function createLangChainTools(options: ToolkitOptions) {
  const toolkit = new DakNodeToolkit(options);
  return toolkit.definitions().map(definition => tool(
    async (input, config) => {
      const signal = config?.signal;
      const result = signal ? await new DakNodeToolkit({ ...options, signal: options.signal ? AbortSignal.any([options.signal, signal]) : signal }).execute(definition.name, input) : await definition.execute(input);
      return JSON.stringify(result);
    },
    { name: `daknode_${definition.name}`, description: definition.description, schema: definition.inputSchema },
  ));
}
