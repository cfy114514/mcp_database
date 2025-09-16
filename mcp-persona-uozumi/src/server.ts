import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListPromptsRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  GetPromptRequestSchema,
  ReadResourceRequestSchema
} from "@modelcontextprotocol/sdk/types.js";
import fs from "node:fs";
import path from "node:path";

const __dirname = path.dirname(new URL(import.meta.url).pathname);
const read = (p: string) => fs.readFileSync(path.resolve(__dirname, "..", p), "utf8");

const PERSONA_URI = "persona://uozumi";
const PERSONA_PATH = "personas_uozumi.md";
const SAFETY_PATH = "personas_safety.md";

const server = new Server(
  { name: "mcp-persona-uozumi", version: "0.1.0" },
  { capabilities: { prompts: {}, resources: {} } }
);

// 设置资源处理器
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: PERSONA_URI,
        name: "Uozumi（中文人设）",
        description: "Uozumi {{char}} 的中文人设模板（带 {{user}} / {{char}} 占位符）",
        mimeType: "text/markdown"
      }
    ]
  };
});

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  if (request.params.uri === PERSONA_URI) {
    return {
      contents: [
        {
          uri: PERSONA_URI,
          mimeType: "text/markdown",
          text: read(PERSONA_PATH)
        }
      ]
    };
  }
  throw new Error(`Unknown resource: ${request.params.uri}`);
});

// 设置提示处理器
server.setRequestHandler(ListPromptsRequestSchema, async () => {
  return {
    prompts: [
      {
        name: "uozumi-system",
        description: "注入 Uozumi（中文人设）为当前会话的 system 指令（带安全叠加）",
        arguments: [
          {
            name: "user",
            description: "当前用户名称或标识（替换 {{user}}）",
            required: true
          },
          {
            name: "char", 
            description: "角色名（替换 {{char}}）",
            required: true
          }
        ]
      }
    ]
  };
});

server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  if (request.params.name === "uozumi-system") {
    const args = request.params.arguments || {};
    const safety = read(SAFETY_PATH);
    let persona = read(PERSONA_PATH);

    persona = persona.replaceAll("{{user}}", String(args.user || "{{user}}"));
    persona = persona.replaceAll("{{char}}", String(args.char || "{{char}}"));

    const content = [safety.trim(), "", persona.trim()].join("\n\n");

    return {
      messages: [
        {
          role: "system",
          content: {
            type: "text",
            text: content
          }
        }
      ]
    };
  }
  throw new Error(`Unknown prompt: ${request.params.name}`);
});

const transport = new StdioServerTransport();
server.connect(transport);
console.error("[mcp-persona-uozumi] started on stdio");
