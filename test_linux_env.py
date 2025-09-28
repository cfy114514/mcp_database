#!/usr/bin/env python3
"""
最小化 Linux 环境验证脚本（被部分启动脚本引用）。
检查 python3 可用、关键模块和当前工作目录写权限。
"""
import os, sys
from pathlib import Path

print("Python:", sys.version)
print("Executable:", sys.executable)
print("CWD:", os.getcwd())

# 简单模块校验
for m in ["fastapi", "requests", "numpy"]:
    try:
        __import__(m)
        print(f"OK: {m}")
    except Exception as e:
        print(f"MISSING: {m} -> {e}")

# 写权限检查
try:
    p = Path(".env.test.writable")
    p.write_text("ok", encoding="utf-8")
    print("Writable: yes")
    p.unlink(missing_ok=True)
except Exception as e:
    print("Writable: no ->", e)
