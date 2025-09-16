#!/usr/bin/env python3
"""
数据库重置工具。
用于清除向量数据库中的所有数据，或者创建数据备份。
"""

import shutil
from pathlib import Path
from datetime import datetime
import argparse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DatabaseReset")

def reset_database(backup: bool = True):
    """重置数据库，可选是否先备份"""
    data_dir = Path("data")
    
    # 如果需要备份
    if backup and data_dir.exists():
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path("backups") / f"backup_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制数据到备份目录
            shutil.copytree(data_dir, backup_dir / "data", dirs_exist_ok=True)
            logger.info(f"数据已备份到: {backup_dir}")
        except Exception as e:
            logger.error(f"备份失败: {e}")
            if input("是否继续重置数据库？(y/N) ").lower() != 'y':
                logger.info("操作已取消")
                return False
    
    # 重置数据目录
    try:
        if data_dir.exists():
            shutil.rmtree(data_dir)
        data_dir.mkdir(exist_ok=True)
        logger.info("数据库已重置")
        return True
    except Exception as e:
        logger.error(f"重置失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="向量数据库重置工具")
    parser.add_argument('--no-backup', action='store_true', help="不创建备份直接重置")
    args = parser.parse_args()
    
    if not args.no_backup:
        print("将在重置前创建备份")
    else:
        print("警告：将直接重置数据库，不创建备份")
        if input("确定要继续吗？(y/N) ").lower() != 'y':
            print("操作已取消")
            return
    
    reset_database(backup=not args.no_backup)

if __name__ == "__main__":
    main()
