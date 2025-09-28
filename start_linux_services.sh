#!/bin/bash
# [DEPRECATED] 此脚本已合并至 manage_linux_services.sh，请改用该脚本

set -e

if [ -x "./manage_linux_services.sh" ]; then
  echo "[NOTICE] start_linux_services.sh 已废弃，转发到 ./manage_linux_services.sh start"
  ./manage_linux_services.sh start
  exit $?
else
  echo "[ERROR] 未找到 manage_linux_services.sh，请从 README 按指南使用 deploy_all_tools.py"
  exit 1
fi
