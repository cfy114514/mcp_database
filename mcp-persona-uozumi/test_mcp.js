#!/usr/bin/env node

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { spawn } from "child_process";

async function testMCP() {
  console.log("正在测试 MCP 服务器...");
  
  // 启动 MCP 服务器进程
  const serverProcess = spawn("node", ["dist/server.js"], {
    cwd: process.cwd(),
    stdio: ["pipe", "pipe", "inherit"]
  });

  try {
    // 创建 stdio transport
    const transport = new StdioClientTransport({
      readable: serverProcess.stdout,
      writable: serverProcess.stdin
    });

    // 创建客户端
    const client = new Client(
      { name: "test-client", version: "1.0.0" },
      { capabilities: {} }
    );

    // 连接到服务器
    await client.connect(transport);
    console.log("✅ 连接成功");

    // 测试工具列表
    try {
      const tools = await client.listTools();
      console.log("🔧 工具列表:", tools);
    } catch (error) {
      console.log("⚠️ 工具列表错误:", error.message);
    }

    // 测试资源列表
    try {
      const resources = await client.listResources();
      console.log("📄 资源列表:", JSON.stringify(resources, null, 2));
    } catch (error) {
      console.log("❌ 资源列表错误:", error.message);
    }

    // 测试提示列表
    try {
      const prompts = await client.listPrompts();
      console.log("💬 提示列表:", JSON.stringify(prompts, null, 2));
    } catch (error) {
      console.log("❌ 提示列表错误:", error.message);
    }

    // 测试读取资源
    try {
      const resource = await client.readResource({ uri: "persona://uozumi" });
      console.log("📖 资源内容:", resource.contents[0].text.substring(0, 100) + "...");
    } catch (error) {
      console.log("❌ 读取资源错误:", error.message);
    }

    // 测试获取提示
    try {
      const prompt = await client.getPrompt({ 
        name: "uozumi-system", 
        arguments: { user: "测试用户", char: "Uozumi" }
      });
      console.log("🎭 提示内容:", prompt.messages[0].content.text.substring(0, 100) + "...");
    } catch (error) {
      console.log("❌ 获取提示错误:", error.message);
    }

  } catch (error) {
    console.error("❌ 测试失败:", error);
  } finally {
    serverProcess.kill();
  }
}

testMCP().catch(console.error);
