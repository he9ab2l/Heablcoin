############################################################
# 📘 文件说明：存储模块初始化
# 本文件实现的功能：多后端存储模块的包初始化
#
# 📋 程序整体伪代码（中文）：
# 1. 初始化依赖模块和配置
# 2. 定义核心类和函数
# 3. 实现主要业务逻辑
# 4. 提供对外接口
# 5. 异常处理与日志记录
#
# 🔄 程序流程图（逻辑流）：
# ┌──────────────┐
# │  模块导入    │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  导出接口    │
# └──────────────┘
#
# 📊 数据管道说明：
# 数据流向：应用层 → 存储适配器 → 外部存储（文件/Redis/Notion/邮件）
#
# 🧩 文件结构：
# - 核心逻辑实现
#
# 🔗 主要依赖：storage
#
# 🕒 创建时间：2025-12-18
############################################################

"""
存储适配层
==========
提供统一的存储接口，支持多种存储后端（Notion、Email、数据库）。
"""

from .base import StorageTarget, StorageResult
from .notion_adapter import NotionAdapter
from .email_adapter import EmailAdapter
from .file_adapter import FileAdapter

__all__ = [
    "StorageTarget",
    "StorageResult",
    "NotionAdapter",
    "EmailAdapter",
    "FileAdapter",
]
