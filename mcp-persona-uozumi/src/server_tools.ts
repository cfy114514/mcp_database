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
      }
    ]
  };
});

// 设置工具调用处理器
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    case "get_uozumi_persona":
      try {
        const persona = read(PERSONA_PATH);
        return {
          content: [
            {
              type: "text",
              text: `# Uozumi 角色人设\n\n${persona}`
            }
          ]
        };
      } catch (error) {
        return {
          content: [
            {
              type: "text", 
              text: `错误：无法读取人设文件 - ${(error as Error).message}`
            }
          ],
          isError: true
        };
      }

    case "get_uozumi_system_prompt":
      try {
        const safety = read(SAFETY_PATH);
        let persona = read(PERSONA_PATH);
        
        const user = String(args?.user || "用户");
        const char = String(args?.char || "Uozumi");
        
        persona = persona.replaceAll("{{user}}", user);
        persona = persona.replaceAll("{{char}}", char);
        
        const systemPrompt = [safety.trim(), "", persona.trim()].join("\n\n");
        
        return {
          content: [
            {
              type: "text",
              text: `# Uozumi 系统提示\n\n以下是完整的系统提示，可以直接复制到 AI 对话的系统消息中：\n\n---\n\n${systemPrompt}\n\n---\n\n参数替换结果：\n- {{user}} → ${user}\n- {{char}} → ${char}`
            }
          ]
        };
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `错误：无法生成系统提示 - ${(error as Error).message}`
            }
          ],
          isError: true
        };
      }

    case "get_safety_guidelines":
      try {
        const safety = read(SAFETY_PATH);
        return {
          content: [
            {
              type: "text",
              text: `# 安全使用指南\n\n${safety}`
            }
          ]
        };
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `错误：无法读取安全指南 - ${(error as Error).message}`
            }
          ],
          isError: true
        };
      }

    default:
      return {
        content: [
          {
            type: "text",
            text: `错误：未知工具 "${name}"`
          }
        ],
        isError: true
      };
  }
});

const transport = new StdioServerTransport();
server.connect(transport);
console.error("[mcp-persona-uozumi] started on stdio");
