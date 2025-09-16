# mcp-persona-uozumi（Uozumi 中文人设 · MCP 服务）

本子模块以 Model Context Protocol (MCP) 暴露两类能力：
- Resources：人设文档（markdown）
- Prompts：一键注入的 System 模板（带 {{user}} / {{char}} 占位符）+ 安全叠加

目的：
- 将长人设从「智能体预设」迁移到 MCP 服务端统一托管
- 在 xiaozhi-client 中通过一次性注入 system，减少维护多个预设与重复粘贴

## 快速开始

### 安装与构建
```bash
cd mcp-persona-uozumi
pnpm i   # 或 npm i / yarn
pnpm build
```

### 启动（stdio 方式）
```bash
node dist/server.js
```

## 暴露能力

- Resource:
  - uri: `persona://uozumi`
  - 内容：`personas/uozumi.md`（中文人设，带 {{user}} / {{char}} 占位符）
- Prompt:
  - 名称：`uozumi-system`
  - 参数：
    - `user`：用户标识（替换 {{user}}）
    - `char`：角色名（替换 {{char}}）
  - 返回：单条 role=system 的消息，内容 = `personas/safety.md` + 渲染后的人设

## 在 xiaozhi-client 对接

不同分支/实现的 xiaozhi-client 略有差异，这里给出通用做法（以 JSON 配置为例）。若你的客户端支持“注册外部 MCP 服务器”的配置项，请添加类似内容：

```json
{
  "servers": {
    "uozumi-persona": {
      "command": "node",
      "args": ["dist/server.js"],
      "cwd": "./mcp-persona-uozumi"
    }
  }
}
```

- 将该片段放入 xiaozhi-client 的 MCP 配置位置（如全局 config、环境变量映射或启动参数）
- 之后在会话中调用 Prompt 注入人设（示例指令，按客户端 UI/命令改写）：
  - 调用：`uozumi-persona.prompt("uozumi-system", {"user":"{{你的用户名}}","char":"Uozumi"})`
  - 作用：在当前会话写入一条 system 消息，之后风格与设定将随会话持续生效（无须每轮重复）

若客户端支持“新建会话自动执行 Prompt”，可将 `uozumi-system` 设为开场注入。

## 精简模式（可选）

当上下文紧张时，可仅注入精简规则。你可以复制 `personas/uozumi.md` 为 `personas/uozumi.compact.md`，保留：
- 口吻/性格三要点
- 安全边界
- 三条说话风格规则
并新增一个 `uozumi-compact` Prompt（同 `server.ts` 的 `addPrompt` 逻辑），在需要时调用。

## 目录
- personas/uozumi.md：中文人设（含占位符）
- personas/safety.md：安全叠加说明
- src/server.ts：MCP 服务（stdio）
- package.json / tsconfig.json：构建配置

## 注意
- 将“破规”类设定用 `safety.md` 统一覆盖，高优先级遵循平台与法律合规。
- 本模块不改变模型计费策略；优势在于减少多预设的复制维护与误注风险。