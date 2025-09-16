# mcp-persona-uozumi（Uozumi 中文人设 · MCP 服务）

本子模块以 Model Context Protocol (MCP) 暴露 Uozumi 角色人设相关的工具能力：
- 🛠️ **工具模式**：提供三个工具函数，适配只支持工具调用的 AI 客户端
- 📄 完整人## 注意事项

- ✅ **工具模式**：本服务器采用工具模式，适配只支持工具调用的 AI 客户端
- 🛡️ **安全合规**：所有人设内容都包含安全指南覆盖，遵循平台与法律合规要求
- 💰 **计费说明**：本模块不改变模型计费策略；优势在于减少多预设的复制维护与误注风险
- 🔧 **兼容性**：如果你的客户端支持资源/提示模式，可以参考 git 历史中的旧版本实现
- 📁 **路径配置**：确保配置文件中的路径指向正确的项目目录

## 常见问题

**Q: 工具列表中看不到 uozumi 相关工具？**
A: 检查 MCP 配置文件路径是否正确，确保服务器成功启动

**Q: 调用工具时出现文件读取错误？**
A: 检查 `personas_uozumi.md` 和 `personas_safety.md` 文件是否存在于项目根目录

**Q: 想要自定义人设内容？**
A: 直接编辑 `personas_uozumi.md` 文件，重新启动服务器即可生效获取
- 🎭 一键生成系统提示（带 {{user}} / {{char}} 占位符替换）
- 🛡️ 安全使用指南

目的：
- 将长人设从「智能体预设」迁移到 MCP 服务端统一托管
- 通过工具调用的方式获取人设内容，适配各种 AI 客户端
- 减少维护多个预设与重复粘贴的工作量

## 快速开始

### 安装与构建
```bash
cd mcp-persona-uozumi
pnpm i   # 或 npm i / yarn
pnpm build
```

### 启动（stdio 方式）
```bash
# 方式一：直接运行
node dist/server.js

# 方式二：使用批处理脚本（Windows）
start.bat

# 方式三：使用 npm
npm start
```

成功启动后，终端会显示：
```
[mcp-persona-uozumi] started on stdio
```

## 暴露能力

### 🛠️ 可用工具

1. **`get_uozumi_persona`**
   - 描述：获取 Uozumi 角色的完整人设内容
   - 参数：无
   - 返回：完整的角色人设文档（Markdown 格式）

2. **`get_uozumi_system_prompt`**
   - 描述：生成 Uozumi 角色的系统提示（包含安全指南和人设）
   - 参数：
     - `user`（可选，字符串）：用户名称，默认 "用户"
     - `char`（可选，字符串）：角色名，默认 "Uozumi"
   - 返回：可直接使用的完整系统提示，包含参数替换结果

3. **`get_safety_guidelines`**
   - 描述：获取安全使用指南
   - 参数：无
   - 返回：安全使用指南文档

### 📝 使用示例

```javascript
// 获取完整人设
const persona = await callTool("get_uozumi_persona");

// 生成自定义系统提示
const systemPrompt = await callTool("get_uozumi_system_prompt", {
  user: "小明",
  char: "Uozumi"
});

// 获取安全指南
const safety = await callTool("get_safety_guidelines");
```

## 在 AI 客户端中对接

### MCP 配置

在支持 MCP 的 AI 客户端中，添加以下配置：

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

### 工具调用方式

配置完成后，你的 AI 客户端应该能在**工具列表**中看到以下三个工具：

- `get_uozumi_persona` - 获取角色人设
- `get_uozumi_system_prompt` - 生成系统提示  
- `get_safety_guidelines` - 获取安全指南

### 推荐使用流程

1. **首次设置**：调用 `get_uozumi_system_prompt` 工具，将返回的内容复制到 AI 对话的系统消息中
2. **查看人设**：需要查看详细人设时，调用 `get_uozumi_persona` 工具
3. **安全提醒**：查看使用注意事项时，调用 `get_safety_guidelines` 工具

## 配置文件说明

项目包含一个配置示例文件 `xiaozhi.mcp.config.example.json`，你可以：

1. 复制为实际配置文件名（如 `config.json`）
2. 根据你的 AI 客户端要求调整路径
3. 确保 `cwd` 路径指向正确的项目目录

## 快速测试

### 验证服务器状态

1. 启动服务器：
   ```bash
   cd mcp-persona-uozumi
   node dist/server.js
   ```

2. 如果看到 `[mcp-persona-uozumi] started on stdio` 说明启动成功

### 在客户端中测试

配置完成后，在你的 AI 客户端中：

1. 查看工具列表，应该能看到三个 `uozumi-persona` 相关的工具
2. 尝试调用 `get_uozumi_system_prompt` 工具
3. 将返回的内容设置为系统消息，开始与 Uozumi 对话

## 目录结构

```
mcp-persona-uozumi/
├── src/
│   └── server.ts           # MCP 服务器主文件
├── dist/
│   └── server.js           # 编译后的文件
├── personas_uozumi.md      # Uozumi 角色人设
├── personas_safety.md     # 安全使用指南
├── start.bat              # Windows 启动脚本
├── package.json           # 项目配置
├── tsconfig.json          # TypeScript 配置
└── README.md              # 本文档
```

## 注意
- 将“破规”类设定用 `safety.md` 统一覆盖，高优先级遵循平台与法律合规。
- 本模块不改变模型计费策略；优势在于减少多预设的复制维护与误注风险。