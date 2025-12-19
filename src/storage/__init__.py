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
