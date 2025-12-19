"""
文件存储适配器
==============
将数据保存到本地文件系统。
"""
from __future__ import annotations
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from storage.base import StorageTarget, StorageResult, StorageType


class FileAdapter(StorageTarget):
    """文件存储适配器"""
    def __init__(self, base_dir: str = "reports"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    @property
    def storage_type(self) -> StorageType:
        return StorageType.FILE
    def _get_dated_dir(self) -> Path:
        """获取按日期组织的目录"""
        date_str = datetime.now().strftime("%Y%m%d")
        dated_dir = self.base_dir / date_str
        dated_dir.mkdir(parents=True, exist_ok=True)
        return dated_dir
    def _generate_filename(self, prefix: str, ext: str = "md") -> str:
        """生成唯一文件名"""
        timestamp = datetime.now().strftime("%H%M%S")
        return f"{prefix}_{timestamp}.{ext}"
    def save_report(self, title: str, content: str, **kwargs) -> StorageResult:
        """保存报告到文件"""
        try:
            # 确定保存目录
            subdir = kwargs.get("subdir", "")
            if subdir:
                save_dir = self.base_dir / subdir
                save_dir.mkdir(parents=True, exist_ok=True)
            else:
                save_dir = self._get_dated_dir()
            # 生成文件名
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')[:50]
            filename = self._generate_filename(safe_title or "report", "md")
            # 保存文件
            filepath = save_dir / filename
            # 添加标题到内容
            full_content = f"# {title}\n\n{content}"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_content)
            return StorageResult(
                success=True,
                storage_type=self.storage_type,
                location=str(filepath.absolute()),
                message=f"Report saved to {filepath}"
            )
        except Exception as e:
            return StorageResult(
                success=False,
                storage_type=self.storage_type,
                location="",
                error=str(e)
            )
    def save_trade_log(self, data: Dict[str, Any], **kwargs) -> StorageResult:
        """保存交易日志"""
        try:
            save_dir = self._get_dated_dir()
            filename = self._generate_filename("trade_log", "json")
            filepath = save_dir / filename
            # 添加时间戳
            data["saved_at"] = datetime.now().isoformat()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return StorageResult(
                success=True,
                storage_type=self.storage_type,
                location=str(filepath.absolute()),
                message=f"Trade log saved to {filepath}"
            )
        except Exception as e:
            return StorageResult(
                success=False,
                storage_type=self.storage_type,
                location="",
                error=str(e)
            )
    def save_analysis(self, symbol: str, analysis: Dict[str, Any], **kwargs) -> StorageResult:
        """保存分析结果"""
        try:
            save_dir = self._get_dated_dir()
            safe_symbol = symbol.replace("/", "_").replace(":", "_")
            filename = self._generate_filename(f"analysis_{safe_symbol}", "json")
            filepath = save_dir / filename
            # 添加元数据
            analysis["symbol"] = symbol
            analysis["saved_at"] = datetime.now().isoformat()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)
            return StorageResult(
                success=True,
                storage_type=self.storage_type,
                location=str(filepath.absolute()),
                message=f"Analysis saved to {filepath}"
            )
        except Exception as e:
            return StorageResult(
                success=False,
                storage_type=self.storage_type,
                location="",
                error=str(e)
            )
