import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import fs from "fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PERSONA_PATH = path.resolve(__dirname, "..", "personas_luoluo.md");
const WORLD_BOOK_PATH = path.resolve(__dirname, "..", "data", "luoluo_worldbook.zh.json");
const SAFETY_PATH = path.resolve(__dirname, "..", "..", "mcp-persona-uozumi", "personas_safety.md");

async function readText(filePath: string) {
  return fs.readFile(filePath, "utf-8");
}

async function readWorldbook() {
  const raw = await fs.readFile(WORLD_BOOK_PATH, "utf-8");
  return JSON.parse(raw) as { meta: any; entries: Array<any> };
}

function replacePlaceholders(text: string, user = "用户", char = "络络") {
  return String(text).replaceAll("{{user}}", user).replaceAll("{{char}}", char);
}

const server = new Server({
  name: "mcp-persona-luoluo",
  version: "1.0.0",
  description: "MCP tools-only server for persona Luoluo",
}, {
  capabilities: { tools: {} },
});

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "get_luoluo_persona",
      description: "获取‘络络’的人设 Markdown 内容。",
      inputSchema: { type: "object", properties: {}, additionalProperties: false },
    },
    {
      name: "get_luoluo_system_prompt",
      description: "返回作为系统提示使用的‘络络’综合提示（含安全规则与占位替换）",
      inputSchema: {
        type: "object",
        properties: {
          user: { type: "string", description: "会话中用户称呼，默认‘用户’" },
          char: { type: "string", description: "角色名，默认‘络络’" },
        },
        additionalProperties: false,
      },
    },
    {
      name: "get_luoluo_safety_guidelines",
      description: "返回通用安全规范（适用于‘络络’）。",
      inputSchema: { type: "object", properties: {}, additionalProperties: false },
    },
    {
      name: "list_luoluo_worldbook_entries",
      description: "列出‘络络’世界书条目摘要。",
      inputSchema: { type: "object", properties: {}, additionalProperties: false },
    },
    {
      name: "get_luoluo_worldbook_entry",
      description: "根据 id 获取完整世界书条目。",
      inputSchema: {
        type: "object",
        properties: { id: { type: "string" } },
        required: ["id"],
        additionalProperties: false,
      },
    },
    {
      name: "search_luoluo_worldbook",
      description: "在‘络络’世界书内进行简单文本检索，返回top_k条命中（含分数）。",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string" },
          top_k: { type: "number", default: 5 },
        },
        required: ["query"],
        additionalProperties: false,
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const name = req.params.name;
  const args = (req.params.arguments ?? {}) as any;
  try {
    switch (name) {
      case "get_luoluo_persona": {
        const md = await readText(PERSONA_PATH);
        return { content: [{ type: "text", text: md }] };
      }
      case "get_luoluo_system_prompt": {
        const [safety, persona] = await Promise.all([
          readText(SAFETY_PATH).catch(() => ""),
          readText(PERSONA_PATH),
        ]);
        const user = args.user || "用户";
        const char = args.char || "络络";
        const merged = `【安全规则】\n${safety}\n\n【角色人设】\n${replacePlaceholders(persona, user, char)}`;
        return { content: [{ type: "text", text: merged }] };
      }
      case "get_luoluo_safety_guidelines": {
        const safety = await readText(SAFETY_PATH);
        return { content: [{ type: "text", text: safety }] };
      }
      case "list_luoluo_worldbook_entries": {
        const wb = await readWorldbook();
        const items = wb.entries.map((e: any) => ({ id: e.id, comment: e.comment, tags: e.tags }));
        return { content: [{ type: "json", json: items }] } as any;
      }
      case "get_luoluo_worldbook_entry": {
        const wb = await readWorldbook();
        const id = String(args.id);
        const entry = wb.entries.find((e: any) => e.id === id);
        if (!entry) throw new Error(`entry not found: ${id}`);
        return { content: [{ type: "json", json: entry }] } as any;
      }
      case "search_luoluo_worldbook": {
        const wb = await readWorldbook();
        const query = String(args.query || "").toLowerCase();
        const topK = Number(args.top_k ?? 5);
        const scored: Array<{ id: string; score: number } & any> = [];
        for (const e of wb.entries) {
          let score = 0;
          const fields: string[] = [];
          if (Array.isArray(e.keys)) fields.push(...e.keys);
          if (e.comment) fields.push(e.comment);
          if (Array.isArray(e.tags)) fields.push(...e.tags);
          if (Array.isArray(e.chunks)) fields.push(...e.chunks.map((c: any) => c.text));
          const hay = fields.join("\n").toLowerCase();
          const hits = hay.includes(query) ? 1 : 0;
          score += hits;
          if (score > 0) scored.push({ id: e.id, comment: e.comment, score });
        }
        scored.sort((a, b) => b.score - a.score);
        return { content: [{ type: "json", json: scored.slice(0, topK) }] } as any;
      }
      default:
        throw new Error(`unknown tool: ${name}`);
    }
  } catch (err) {
    const msg = (err as Error).message || String(err);
    return { isError: true, content: [{ type: "text", text: `error: ${msg}` }] } as any;
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
console.error("[mcp-persona-luoluo] started on stdio");
