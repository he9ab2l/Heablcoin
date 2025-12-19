############################################################
# 📘 文件说明：
# 本文件实现的功能：Notion 存储适配器
#
# 📋 程序整体伪代码（中文）：
# 1. 初始化主要依赖与变量
# 2. 加载输入数据或接收外部请求
# 3. 执行主要逻辑步骤（如计算、处理、训练、渲染等）
# 4. 输出或返回结果
# 5. 异常处理与资源释放
#
# 🔄 程序流程图（逻辑流）：
# ┌──────────┐
# │  输入数据 │
# └─────┬────┘
#       ↓
# ┌────────────┐
# │  核心处理逻辑 │
# └─────┬──────┘
#       ↓
# ┌──────────┐
# │  输出结果 │
# └──────────┘
#
# 📊 数据管道说明：
# 数据流向：输入源 → 数据清洗/转换 → 核心算法模块 → 输出目标（文件 / 接口 / 终端）
#
# 🧩 文件结构：
# - 依赖（标准库）：__future__, datetime, json, os, typing
# - 依赖（第三方）：无
# - 依赖（本地）：storage.base
#
# 🕒 创建时间：2025-12-19
############################################################

"""
Notion 存储适配器
=================
将数据保存到 Notion 数据库。
需要配置 NOTION_API_KEY 和 NOTION_DATABASE_ID。
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from storage.base import StorageTarget, StorageResult, StorageType

try:
    import urllib.request
    import urllib.error
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False


class NotionAdapter(StorageTarget):
    """Notion 存储适配器"""
    
    NOTION_API_VERSION = "2022-06-28"
    NOTION_API_BASE = "https://api.notion.com/v1"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        database_id: Optional[str] = None,
        reports_db_id: Optional[str] = None,
        trades_db_id: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("NOTION_API_KEY", "")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID", "")
        self.reports_db_id = reports_db_id or os.getenv("NOTION_REPORTS_DB_ID", self.database_id)
        self.trades_db_id = trades_db_id or os.getenv("NOTION_TRADES_DB_ID", self.database_id)
    
    @property
    def storage_type(self) -> StorageType:
        return StorageType.NOTION
    
    def is_available(self) -> bool:
        """检查 Notion 是否可用"""
        return bool(self.api_key and self.database_id)
    
    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict] = None
    ) -> Dict:
        """发送 Notion API 请求"""
        if not HAS_URLLIB:
            raise RuntimeError("urllib not available")
        
        url = f"{self.NOTION_API_BASE}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.NOTION_API_VERSION,
        }
        
        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Notion API error: {e.code} - {error_body}")
    
    def _markdown_to_blocks(self, content: str, max_length: int = 2000) -> List[Dict]:
        """将 Markdown 转换为 Notion blocks"""
        blocks = []
        
        # 简单分段处理
        paragraphs = content.split("\n\n")
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 处理标题
            if para.startswith("# "):
                blocks.append({
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": para[2:]}}]
                    }
                })
            elif para.startswith("## "):
                blocks.append({
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": para[3:]}}]
                    }
                })
            elif para.startswith("### "):
                blocks.append({
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": para[4:]}}]
                    }
                })
            elif para.startswith("- ") or para.startswith("* "):
                # 列表项
                items = para.split("\n")
                for item in items:
                    item_text = item.lstrip("- *").strip()
                    if item_text:
                        blocks.append({
                            "type": "bulleted_list_item",
                            "bulleted_list_item": {
                                "rich_text": [{"type": "text", "text": {"content": item_text[:max_length]}}]
                            }
                        })
            elif para.startswith("```"):
                # 代码块
                lines = para.split("\n")
                code_content = "\n".join(lines[1:-1]) if len(lines) > 2 else ""
                blocks.append({
                    "type": "code",
                    "code": {
                        "rich_text": [{"type": "text", "text": {"content": code_content[:max_length]}}],
                        "language": "plain text"
                    }
                })
            else:
                # 普通段落
                blocks.append({
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": para[:max_length]}}]
                    }
                })
        
        return blocks[:100]  # Notion 限制每次最多100个块
    
    def save_report(self, title: str, content: str, **kwargs) -> StorageResult:
        """保存报告到 Notion"""
        if not self.is_available():
            return StorageResult(
                success=False,
                storage_type=self.storage_type,
                location="",
                error="Notion API key or database ID not configured"
            )
        
        try:
            # 创建页面
            page_data = {
                "parent": {"database_id": self.reports_db_id},
                "properties": {
                    "Title": {
                        "title": [{"text": {"content": title}}]
                    },
                    "Type": {
                        "select": {"name": kwargs.get("report_type", "Report")}
                    },
                    "Created": {
                        "date": {"start": datetime.now().isoformat()}
                    }
                },
                "children": self._markdown_to_blocks(content)
            }
            
            # 添加额外属性
            if "symbol" in kwargs:
                page_data["properties"]["Symbol"] = {
                    "rich_text": [{"text": {"content": kwargs["symbol"]}}]
                }
            
            result = self._make_request("/pages", method="POST", data=page_data)
            
            page_url = result.get("url", "")
            page_id = result.get("id", "")
            
            return StorageResult(
                success=True,
                storage_type=self.storage_type,
                location=page_url,
                message=f"Report saved to Notion",
                metadata={"page_id": page_id}
            )
            
        except Exception as e:
            return StorageResult(
                success=False,
                storage_type=self.storage_type,
                location="",
                error=str(e)
            )

    def append_daily_log(self, content: str, title: Optional[str] = None, tags: Optional[List[str]] = None) -> StorageResult:
        """追加一条日记/日志到 reports 数据库（可复用主库 ID）。"""
        if not self.is_available():
            return StorageResult(
                success=False,
                storage_type=self.storage_type,
                location="",
                error="Notion API key or database ID not configured"
            )
        page_title = title or "Session Log"
        tags = tags or []
        try:
            data = {
                "parent": {"database_id": self.reports_db_id},
                "properties": {
                    "Title": {"title": [{"text": {"content": page_title}}]},
                    "Tags": {"multi_select": [{"name": t} for t in tags]},
                },
                "children": self._markdown_to_blocks(content),
            }
            result = self._make_request("/pages", method="POST", data=data)
            return StorageResult(
                success=True,
                storage_type=self.storage_type,
                location=result.get("url", ""),
                metadata={"page_id": result.get("id", ""), "tags": tags},
                message="Log saved to Notion"
            )
        except Exception as e:
            return StorageResult(
                success=False,
                storage_type=self.storage_type,
                location="",
                error=str(e)
            )
    
    def save_trade_log(self, data: Dict[str, Any], **kwargs) -> StorageResult:
        """保存交易日志到 Notion"""
        if not self.is_available():
            return StorageResult(
                success=False,
                storage_type=self.storage_type,
                location="",
                error="Notion API key or database ID not configured"
            )
        
        try:
            # 创建数据库条目
            page_data = {
                "parent": {"database_id": self.trades_db_id},
                "properties": {
                    "Title": {
                        "title": [{"text": {"content": f"Trade: {data.get('symbol', 'Unknown')}"}}]
                    },
                    "Symbol": {
                        "rich_text": [{"text": {"content": data.get("symbol", "")}}]
                    },
                    "Side": {
                        "select": {"name": data.get("side", "unknown")}
                    },
                    "Amount": {
                        "number": float(data.get("amount", 0))
                    },
                    "Price": {
                        "number": float(data.get("price", 0))
                    },
                    "Date": {
                        "date": {"start": data.get("timestamp", datetime.now().isoformat())}
                    }
                }
            }
            
            result = self._make_request("/pages", method="POST", data=page_data)
            
            return StorageResult(
                success=True,
                storage_type=self.storage_type,
                location=result.get("url", ""),
                message="Trade log saved to Notion",
                metadata={"page_id": result.get("id", "")}
            )
            
        except Exception as e:
            return StorageResult(
                success=False,
                storage_type=self.storage_type,
                location="",
                error=str(e)
            )
    
    def save_analysis(self, symbol: str, analysis: Dict[str, Any], **kwargs) -> StorageResult:
        """保存分析结果到 Notion"""
        # 将分析结果格式化为报告
        content = f"""## 分析摘要

**交易对**: {symbol}
**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 分析结果

```json
{json.dumps(analysis, ensure_ascii=False, indent=2)}
```
"""
        return self.save_report(
            title=f"{symbol} 分析报告",
            content=content,
            report_type="Analysis",
            symbol=symbol,
            **kwargs
        )
