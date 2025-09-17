import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema
} from "@modelcontextprotocol/sdk/types.js";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const read = (p: string) => fs.readFileSync(path.resolve(__dirname, "..", p), "utf8");

const PERSONA_PATH = "personas_uozumi.md";
const SAFETY_PATH = "personas_safety.md";
// 新增：世界书路径
const WORLD_BOOK_PATH = "data/uozumi_worldbook.zh.json";

// 新增：引入“络络”文件的绝对路径（同一仓库的兄弟目录）
const LUOLOO_PERSONA_PATH = path.resolve(__dirname, "..", "..", "mcp-persona-luoluo", "personas_luoluo.md");
const LUOLOO_WORLD_BOOK_PATH = path.resolve(__dirname, "..", "..", "mcp-persona-luoluo", "data", "luoluo_worldbook.zh.json");
const readAbs = (absPath: string) => fs.readFileSync(absPath, "utf8");

const server = new Server(
  { name: "mcp-persona-uozumi", version: "0.1.0" },
  { capabilities: { tools: {} } }
);

// 设置工具列表处理器
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "get_uozumi_persona",
        description: "获取 Uozumi 角色的完整人设内容",
        inputSchema: {
          type: "object",
          properties: {},
          required: []
        }
      },
      {
        name: "get_uozumi_system_prompt", 
        description: "生成 Uozumi 角色的系统提示（包含安全指南和人设）",
        inputSchema: {
          type: "object",
          properties: {
            user: {
              type: "string",
              description: "当前用户名称或标识（替换 {{user}}）",
              default: "用户"
            },
            char: {
              type: "string", 
              description: "角色名（替换 {{char}}）",
              default: "Uozumi"
            }
          },
          required: []
        }
      },
      {
        name: "get_safety_guidelines",
        description: "获取安全使用指南",
        inputSchema: {
          type: "object",
          properties: {},
          required: []
        }
      },
      // --- 新增：Luoluo 工具 ---
      {
        name: "get_luoluo_persona",
        description: "获取 Luoluo 角色的完整人设内容",
        inputSchema: { type: "object", properties: {}, required: [] }
      },
      {
        name: "get_luoluo_system_prompt",
        description: "生成 Luoluo 角色的系统提示（包含安全指南和人设）",
        inputSchema: {
          type: "object",
          properties: {
            user: { type: "string", description: "当前用户名称（替换 {{user}}）", default: "用户" },
            char: { type: "string", description: "角色名（替换 {{char}}）", default: "络络" }
          },
          required: []
        }
      },
      {
        name: "get_luoluo_safety_guidelines",
        description: "获取安全使用指南（络络）",
        inputSchema: { type: "object", properties: {}, required: [] }
      },
      {
        name: "list_luoluo_worldbook_entries",
        description: "列出 Luoluo 世界书条目（基本信息）",
        inputSchema: { type: "object", properties: {}, required: [] }
      },
      {
        name: "get_luoluo_worldbook_entry",
        description: "获取 Luoluo 指定世界书条目（含分块）",
        inputSchema: { type: "object", properties: { id: { type: "string" } }, required: ["id"] }
      },
      {
        name: "search_luoluo_worldbook",
        description: "在 Luoluo 世界书中按关键词检索（字符串匹配）",
        inputSchema: { type: "object", properties: { query: { type: "string" }, top_k: { type: "number", default: 5 } }, required: ["query"] }
      },
      // --- Uozumi 原有世界书工具 ---
      {
        name: "list_worldbook_entries",
        description: "列出世界书条目（基本信息）",
        inputSchema: { type: "object", properties: {}, required: [] }
      },
      {
        name: "get_worldbook_entry",
        description: "获取指定世界书条目（含分块）",
        inputSchema: {
          type: "object",
          properties: { id: { type: "string", description: "条目ID" } },
          required: ["id"]
        }
      },
      {
        name: "search_worldbook",
        description: "按关键词在世界书中检索（基于字符串匹配）",
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string", description: "检索关键词" },
            top_k: { type: "number", description: "返回数量上限", default: 5 }
          },
          required: ["query"]
        }
      }
    ]
  };
});

// 设置工具调用处理器
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  // 帮助函数：读取世界书
  const readWorldbook = () => {
    try {
      const raw = read(WORLD_BOOK_PATH);
      return JSON.parse(raw) as { entries: any[] };
    } catch (e) {
      return null;
    }
  };

  switch (name) {
    // --- Uozumi 原有 ---
    case "get_uozumi_persona":
      try {
        const persona = read(PERSONA_PATH);
        return {
          content: [
            { type: "text", text: `# Uozumi 角色人设\n\n${persona}` }
          ]
        };
      } catch (error) {
        return { content: [{ type: "text", text: `错误：无法读取人设文件 - ${(error as Error).message}` }], isError: true };
      }

    case "get_uozumi_system_prompt":
      try {
        const safety = read(SAFETY_PATH);
        let persona = read(PERSONA_PATH);
        const user = String(args?.user || "用户");
        const char = String(args?.char || "Uozumi");
        persona = persona.replaceAll("{{user}}", user).replaceAll("{{char}}", char);
        const systemPrompt = [safety.trim(), "", persona.trim()].join("\n\n");
        return {
          content: [
            { type: "text", text: `# Uozumi 系统提示\n\n${systemPrompt}` }
          ]
        };
      } catch (error) {
        return { content: [{ type: "text", text: `错误：无法生成系统提示 - ${(error as Error).message}` }], isError: true };
      }

    case "get_safety_guidelines":
      try {
        const safety = read(SAFETY_PATH);
        return { content: [{ type: "text", text: `# 安全使用指南\n\n${safety}` }] };
      } catch (error) {
        return { content: [{ type: "text", text: `错误：无法读取安全指南 - ${(error as Error).message}` }], isError: true };
      }

    // --- 新增：Luoluo ---
    case "get_luoluo_persona":
      try {
        const persona = readAbs(LUOLOO_PERSONA_PATH);
        return { content: [{ type: "text", text: `# Luoluo 角色人设\n\n${persona}` }] };
      } catch (error) {
        return { content: [{ type: "text", text: `错误：无法读取 Luoluo 人设 - ${(error as Error).message}` }], isError: true };
      }

    case "get_luoluo_system_prompt":
      try {
        const safety = read(SAFETY_PATH);
        let persona = readAbs(LUOLOO_PERSONA_PATH);
        const user = String(args?.user || "用户");
        const char = String(args?.char || "络络");
        persona = persona.replaceAll("{{user}}", user).replaceAll("{{char}}", char);
        const systemPrompt = [safety.trim(), "", persona.trim()].join("\n\n");
        return { content: [{ type: "text", text: `# Luoluo 系统提示\n\n${systemPrompt}` }] };
      } catch (error) {
        return { content: [{ type: "text", text: `错误：无法生成 Luoluo 系统提示 - ${(error as Error).message}` }], isError: true };
      }

    case "get_luoluo_safety_guidelines":
      try {
        const safety = read(SAFETY_PATH);
        return { content: [{ type: "text", text: `# Luoluo 安全使用指南\n\n${safety}` }] };
      } catch (error) {
        return { content: [{ type: "text", text: `错误：无法读取 Luoluo 安全指南 - ${(error as Error).message}` }], isError: true };
      }

    case "list_luoluo_worldbook_entries": {
      try {
        const raw = readAbs(LUOLOO_WORLD_BOOK_PATH);
        const wb = JSON.parse(raw) as { entries: any[] };
        const summary = (wb.entries || []).map((e: any) => ({ id: e.id, keys: e.keys, comment: e.comment, tags: e.tags, chunkCount: Array.isArray(e.chunks) ? e.chunks.length : 0 }));
        return { content: [{ type: "text", text: JSON.stringify({ entries: summary }, null, 2) }] };
      } catch (e) {
        return { content: [{ type: "text", text: `错误：无法读取 Luoluo 世界书 - ${(e as Error).message}` }], isError: true };
      }
    }

    case "get_luoluo_worldbook_entry": {
      try {
        const raw = readAbs(LUOLOO_WORLD_BOOK_PATH);
        const wb = JSON.parse(raw) as { entries: any[] };
        const id = String(args?.id || "");
        const found = (wb.entries || []).find((e: any) => e.id === id);
        if (!found) return { content: [{ type: "text", text: `未找到 Luoluo 条目：${id}` }], isError: true };
        return { content: [{ type: "text", text: JSON.stringify(found, null, 2) }] };
      } catch (e) {
        return { content: [{ type: "text", text: `错误：读取 Luoluo 条目失败 - ${(e as Error).message}` }], isError: true };
      }
    }

    case "search_luoluo_worldbook": {
      try {
        const raw = readAbs(LUOLOO_WORLD_BOOK_PATH);
        const wb = JSON.parse(raw) as { entries: any[] };
        const query = String(args?.query || "").toLowerCase();
        const topK = Math.max(1, Number(args?.top_k ?? 5));
        const results: Array<{ score: number; entryId: string; chunkId?: string; text?: string }> = [];
        for (const e of wb.entries || []) {
          const keys = (e.keys || []).join(" ").toLowerCase();
          const comment = String(e.comment || "").toLowerCase();
          let entryScore = 0;
          if (keys.includes(query)) entryScore += 2;
          if (comment.includes(query)) entryScore += 1;
          if (entryScore > 0) results.push({ score: entryScore, entryId: e.id });
          if (Array.isArray(e.chunks)) {
            for (const c of e.chunks) {
              const txt = String(c.text || "").toLowerCase();
              if (txt.includes(query)) results.push({ score: 3, entryId: e.id, chunkId: c.id, text: c.text });
            }
          }
        }
        results.sort((a, b) => b.score - a.score);
        return { content: [{ type: "text", text: JSON.stringify({ query, results: results.slice(0, topK) }, null, 2) }] };
      } catch (e) {
        return { content: [{ type: "text", text: `错误：检索 Luoluo 世界书失败 - ${(e as Error).message}` }], isError: true };
      }
    }

    default:
      return { content: [{ type: "text", text: `错误：未知工具 "${name}"` }], isError: true };
  }
});

const transport = new StdioServerTransport();
server.connect(transport);
console.error("[mcp-persona-uozumi] started on stdio");
