#!/usr/bin/env bash
# 简易 Ubuntu 一键部署脚本（最小可用版）
# 作用：安装依赖 + 启动/停止/状态 三个本地服务
# - 记忆库工具 (8001)  knowledge_base_service.py
# - 向量数据库工具 (8100) knowledge_base_service.py
# - 角色人设服务 (可选)   mcp-persona-uozumi/dist/server.js
#
# 用法：
#   bash deploy_ubuntu_min.sh install     # 安装依赖（自动创建 .venv）
#   bash deploy_ubuntu_min.sh start       # 启动所有服务
#   bash deploy_ubuntu_min.sh stop        # 停止所有服务
#   bash deploy_ubuntu_min.sh status      # 查看状态
#   bash deploy_ubuntu_min.sh logs        # 快速查看日志路径
#   bash deploy_ubuntu_min.sh restart     # 重启所有服务
#
set -Eeuo pipefail

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/pids"
VENV_DIR="$PROJECT_ROOT/.venv"
PY="$VENV_DIR/bin/python"
NODE_CMD="node"

MEM_NAME="记忆库工具"
VEC_NAME="向量数据库工具"
PER_NAME="角色人设服务"

MEM_PORT=8001
VEC_PORT=8100

MEM_PID_FILE="$PID_DIR/memory_library.pid"
VEC_PID_FILE="$PID_DIR/vector_database.pid"
PER_PID_FILE="$PID_DIR/persona_service.pid"

MEM_LOG="$LOG_DIR/memory_library.log"
VEC_LOG="$LOG_DIR/vector_database.log"
PER_LOG="$LOG_DIR/persona_service.log"

ensure_dirs() {
  mkdir -p "$LOG_DIR" "$PID_DIR"
}

have_cmd() { command -v "$1" >/dev/null 2>&1; }

warn_api_key() {
  # EMBEDDING_API_KEY 缺失时仅警告（服务可启动，生成嵌入时才需要）
  if ! grep -q "^EMBEDDING_API_KEY=" "$PROJECT_ROOT/.env" 2>/dev/null; then
    echo "[WARN] 未在 .env 配置 EMBEDDING_API_KEY，相关生成嵌入操作将失败。"
  fi
}

create_env_file() {
  if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
    cat > "$PROJECT_ROOT/.env" << 'EOF'
KB_PORT=8001
EMBEDDING_API_KEY=
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
# SiliconFlow API 固定为如下地址（代码中已固定此 URL）
# EMBEDDING_API_BASE=https://api.siliconflow.cn/v1
EOF
    echo "[OK] 已创建 .env（请按需填写 EMBEDDING_API_KEY）"
  fi
}

install_python() {
  echo "[INFO] 准备 Python 虚拟环境与依赖..."
  if [[ ! -d "$VENV_DIR" ]]; then
    python3 -m venv "$VENV_DIR"
  fi
  source "$VENV_DIR/bin/activate"
  python -m pip install -U pip setuptools wheel
  if [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
    pip install -r "$PROJECT_ROOT/requirements.txt"
  else
    # 最小依赖回退
    pip install fastapi uvicorn numpy requests python-dotenv pydantic faiss-cpu
  fi
  # 确保 faiss 可用
  (python - << 'PY'
try:
    import faiss  # noqa: F401
    print('faiss ok')
except Exception as e:
    raise SystemExit(1)
PY
  ) || pip install faiss-cpu
}

install_node_optional() {
  # 可选的人设服务依赖
  local dir="$PROJECT_ROOT/mcp-persona-uozumi"
  if [[ -d "$dir" ]] && have_cmd npm; then
    echo "[INFO] 安装人设服务依赖..."
    (cd "$dir" && npm ci && npm run build)
  else
    echo "[INFO] 略过人设服务依赖（目录不存在或未安装 Node.js/npm）"
  fi
}

install_all() {
  ensure_dirs
  create_env_file
  install_python
  install_node_optional
  warn_api_key
  echo "[OK] 依赖安装完成"
}

is_running_pid() { # pid
  [[ -n "${1:-}" ]] || return 1
  kill -0 "$1" 2>/dev/null
}

start_one_py_service() { # name port pid_file log_file
  local name="$1" port="$2" pidf="$3" logf="$4"
  if [[ -f "$pidf" ]] && is_running_pid "$(cat "$pidf" 2>/dev/null || true)"; then
    echo "[SKIP] $name 已在运行 (PID $(cat "$pidf"))"
    return 0
  fi
  echo "[INFO] 启动 $name (:$port) ..."
  source "$VENV_DIR/bin/activate"
  PYTHONUTF8=1 PYTHONIOENCODING=utf-8 KB_PORT="$port" nohup "$PY" "$PROJECT_ROOT/knowledge_base_service.py" \
    >"$logf" 2>&1 & echo $! > "$pidf"
  sleep 2
  # 健康探测：/health 或 /docs
  if curl -sf "http://127.0.0.1:$port/health" >/dev/null || curl -sf "http://127.0.0.1:$port/docs" >/dev/null; then
    echo "[OK] $name 启动成功 (PID $(cat "$pidf"))，日志: $logf"
  else
    echo "[ERR] $name 健康检查失败，查看日志: $logf"
    return 1
  fi
}

start_persona() {
  local dir="$PROJECT_ROOT/mcp-persona-uozumi"
  if [[ ! -d "$dir" ]] || ! have_cmd "$NODE_CMD"; then
    echo "[INFO] 略过启动人设服务（目录不存在或 node 不可用）"
    return 0
  fi
  # 仅在 dist 存在时启动
  if [[ ! -f "$dir/dist/server.js" ]]; then
    echo "[WARN] 未找到 $dir/dist/server.js，跳过启动（请先 npm run build）"
    return 0
  fi
  if [[ -f "$PER_PID_FILE" ]] && is_running_pid "$(cat "$PER_PID_FILE" 2>/dev/null || true)"; then
    echo "[SKIP] $PER_NAME 已在运行 (PID $(cat "$PER_PID_FILE"))"
    return 0
  fi
  echo "[INFO] 启动 $PER_NAME ..."
  nohup "$NODE_CMD" "$dir/dist/server.js" >"$PER_LOG" 2>&1 & echo $! > "$PER_PID_FILE"
  sleep 1
  if is_running_pid "$(cat "$PER_PID_FILE" 2>/dev/null || true)"; then
    echo "[OK] $PER_NAME 启动成功 (PID $(cat "$PER_PID_FILE"))，日志: $PER_LOG"
  else
    echo "[ERR] $PER_NAME 启动失败，日志: $PER_LOG"
  fi
}

start_all() {
  ensure_dirs
  start_one_py_service "$MEM_NAME" "$MEM_PORT" "$MEM_PID_FILE" "$MEM_LOG"
  start_one_py_service "$VEC_NAME" "$VEC_PORT" "$VEC_PID_FILE" "$VEC_LOG"
  start_persona || true
}

stop_one() { # name pid_file
  local name="$1" pidf="$2"
  if [[ -f "$pidf" ]]; then
    local pid
    pid=$(cat "$pidf" 2>/dev/null || true)
    if is_running_pid "$pid"; then
      echo "[INFO] 停止 $name (PID $pid) ..."
      kill "$pid" 2>/dev/null || true
      sleep 1
      if is_running_pid "$pid"; then
        echo "[INFO] 强制结束 $name (PID $pid) ..."
        kill -9 "$pid" 2>/dev/null || true
      fi
    fi
    rm -f "$pidf"
  else
    echo "[SKIP] $name 未运行"
  fi
}

stop_all() {
  stop_one "$MEM_NAME" "$MEM_PID_FILE"
  stop_one "$VEC_NAME" "$VEC_PID_FILE"
  stop_one "$PER_NAME" "$PER_PID_FILE"
}

status_one() { # name port pid_file log
  local name="$1" port="$2" pidf="$3" logf="$4"
  local pid="-"
  if [[ -f "$pidf" ]]; then pid=$(cat "$pidf" 2>/dev/null || echo -); fi
  local http="DOWN"
  if curl -sf "http://127.0.0.1:$port/health" >/dev/null || curl -sf "http://127.0.0.1:$port/docs" >/dev/null; then
    http="UP"
  fi
  if [[ "$port" -eq 0 ]]; then http="N/A"; fi
  if [[ "$pid" != "-" ]] && is_running_pid "$pid"; then
    echo "[RUNNING] $name  PID=$pid  HTTP=$http  LOG=$logf"
  else
    echo "[STOPPED] $name  HTTP=$http  LOG=$logf"
  fi
}

status_all() {
  status_one "$MEM_NAME" "$MEM_PORT" "$MEM_PID_FILE" "$MEM_LOG"
  status_one "$VEC_NAME" "$VEC_PORT" "$VEC_PID_FILE" "$VEC_LOG"
  # persona 无 HTTP 健康接口，端口设 0
  local per_pid="-"; [[ -f "$PER_PID_FILE" ]] && per_pid=$(cat "$PER_PID_FILE" 2>/dev/null || echo -)
  if [[ "$per_pid" != "-" ]] && is_running_pid "$per_pid"; then
    echo "[RUNNING] $PER_NAME  PID=$per_pid  LOG=$PER_LOG"
  else
    echo "[STOPPED] $PER_NAME  LOG=$PER_LOG"
  fi
}

show_logs_hint() {
  echo "日志路径："
  echo "  $MEM_NAME -> $MEM_LOG"
  echo "  $VEC_NAME -> $VEC_LOG"
  echo "  $PER_NAME -> $PER_LOG"
}

case "${1:-}" in
  install)
    install_all
    ;;
  start)
    start_all
    ;;
  stop)
    stop_all
    ;;
  restart)
    stop_all || true
    start_all
    ;;
  status)
    status_all
    ;;
  logs)
    show_logs_hint
    ;;
  *)
    echo "用法: bash $(basename "$0") {install|start|stop|restart|status|logs}"
    exit 1
    ;;
esac
