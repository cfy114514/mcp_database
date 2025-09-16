import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { Resource } from "@modelcontextprotocol/sdk/types.js";
import fs from "node:fs";
import path from "node:path";

const __dirname = path.dirname(new URL(import.meta.url).pathname);
const read = (p: string) => fs.readFileSync(path.resolve(__dirname, "..", p), "utf8");

const PERSONA_URI = "persona://uozumi";
const PERSONA_PATH = "personas/uozumi.md";
const SAFETY_PATH = "personas/safety.md";

const server = new Server(
  { name: "mcp-persona-uozumi", version: "0.1.0" },
  { capabilities: { prompts: {}, resources: {} } }
);

// 资源：人设
server.addResource({
  uri: PERSONA_URI,
  name: "Uozumi（中文人设）",
  description: "Uozumi {{char}} 的中文人设模板（带 {{user}} / {{char}} 占位符）",
  mimeType: "text/markdown",
  get: async () => ({
    contents: [
      {
        uri: PERSONA_URI,
        mimeType: "text/markdown",
        text: read(PERSONA_PATH)
      }
    ]
  })
} as Resource);

// Prompt：人设 + 安全说明（作为 system 注入）
server.addPrompt("uozumi-system", {
  description: "注入 Uozumi（中文人设）为当前会话的 system 指令（带安全叠加）",
  arguments: {
    user: { type: "string", description: "当前用户名称或标识（替换 {{user}}）", required: true },
    char: { type: "string", description: "角色名（替换 {{char}}）", required: true }
  },
  handler: async (args) => {
    const safety = read(SAFETY_PATH);
    let persona = read(PERSONA_PATH);

    persona = persona.replaceAll("{{user}}", String(args.user));
    persona = persona.replaceAll("{{char}}", String(args.char));

    const content = [safety.trim(), "", persona.trim()].join("\n\n");

    return { messages: [{ role: "system", content }] };
  }
});

const transport = new StdioServerTransport();
server.connect(transport);
console.error("[mcp-persona-uozumi] started on stdio");