# MCP Persona: 络络 (Luoluo)

独立的 MCP 工具型服务器，提供：
- get_luoluo_persona：返回人设 Markdown
- get_luoluo_system_prompt：合成系统提示（安全规则 + 人设，占位 {{user}}/{{char}} 替换）
- list_luoluo_worldbook_entries：列出世界书条目摘要
- get_luoluo_worldbook_entry：按 id 获取完整条目
- search_luoluo_worldbook：简单关键词检索

## 目录结构
- personas_luoluo.md
- data/luoluo_worldbook.zh.json
- src/server.ts（MCP stdio server）

## 开发与运行
1) 安装依赖并构建
   - Windows PowerShell：
     - cd ./mcp-persona-luoluo; npm install; npm run build
2) 启动（供 MCP 客户端连接）
   - node ./dist/server.js

> 注意
- 本项目复用上级目录下的 `mcp-persona-uozumi/personas_safety.md` 作为通用安全规则。如需为“络络”单独定制安全规则，请新增文件并在 `src/server.ts` 调整 SAFETY_PATH。

## MCP 客户端配置示例（相对路径）
将工作目录设为仓库根（mcp_database），然后在客户端中配置：

- 命令：node
- 参数：[
  "./mcp-persona-luoluo/dist/server.js"
]

## 工具用法建议
- 启动后，先调用 get_luoluo_system_prompt，传入 { user: "阿漠", char: "络络" }，将返回文本作为系统提示。
- 当涉及设定/背景/互动话术时，先 search_luoluo_worldbook 命中后，再 get_luoluo_worldbook_entry 读取详情。
