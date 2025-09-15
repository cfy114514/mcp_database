#!/usr/bin/env python3
import os
from import_tool import import_documents_from_file
from knowledge_base_service import VectorDatabase

def main():
    # 初始化数据库
    db = VectorDatabase()
    
    # 导入文本文件
    print("\n=== 导入文本教程 ===")
    result = import_documents_from_file(
        db=db,
        file_path="example_docs/python_tutorial.txt",
        default_tags=["Python", "教程"]
    )
    print("文本导入结果:", result)
    
    # 导入JSON文档
    print("\n=== 导入技术文章 ===")
    result = import_documents_from_file(
        db=db,
        file_path="example_docs/tech_articles.json",
        default_tags=["技术文档"]  # 这些标签会与JSON中的标签合并
    )
    print("JSON导入结果:", result)

if __name__ == "__main__":
    main()
