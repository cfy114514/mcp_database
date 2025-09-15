#!/bin/bash

# 设置工作目录
WORK_DIR=/home/xiaozhi/mcp_database/mcp-calculator
LOG_DIR=/home/xiaozhi/logs

# 创建必要的目录
mkdir -p $WORK_DIR
mkdir -p $LOG_DIR
mkdir -p $WORK_DIR/data

# 复制文件到工作目录
cp -r ./* $WORK_DIR/

# 设置权限
chmod +x $WORK_DIR/vector_db.py
chmod +x $WORK_DIR/knowledge_base_service.py

echo "部署完成！"
echo "请在xiaozhi studio中配置EMBEDDING_API_KEY后启动服务"
