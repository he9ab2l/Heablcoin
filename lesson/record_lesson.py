from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


_BEIJING_TZ = timezone(timedelta(hours=8))


@dataclass(frozen=True)
class LessonRecord:
    title: str
    module: str
    environment: str
    phenomenon: str
    root_cause: str
    solution_steps: str


def _beijing_timestamp_for_filename(dt: datetime) -> str:
    return dt.astimezone(_BEIJING_TZ).strftime("%Y%m%d_%H%M")


def _beijing_timestamp_human(dt: datetime) -> str:
    return dt.astimezone(_BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _sanitize_filename(name: str) -> str:
    name = name.strip()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[\\/:*?\"<>|]+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name[:80] if len(name) > 80 else name


def render_markdown(record: LessonRecord, now: datetime) -> str:
    when = _beijing_timestamp_human(now)
    header = f"{record.title}，发生时间：{when}，模块位置：{record.module}，架构环境：{record.environment}".strip()

    return (
        f"{header}\n"
        "---\n"
        "### 问题描述\n"
        f"{record.phenomenon.strip()}\n\n"
        "### 根本原因分析\n"
        f"{record.root_cause.strip()}\n\n"
        "### 解决方案与步骤\n"
        f"{record.solution_steps.strip()}\n"
    )


def write_lesson(record: LessonRecord, output_dir: str | Path = "lesson", now: datetime | None = None) -> Path:
    now = now or datetime.now(tz=_BEIJING_TZ)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_title = _sanitize_filename(record.title) or "问题"
    ts = _beijing_timestamp_for_filename(now)
    filename = f"{safe_title}_{ts}.md"

    path = out_dir / filename
    content = render_markdown(record, now)
    path.write_text(content, encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a lesson postmortem Markdown file under lesson/.")
    parser.add_argument("--title", required=True, help="问题描述标题（用于文件名与标题行）")
    parser.add_argument("--module", required=True, help="代码模块位置，例如 utils/smart_logger.py:123")
    parser.add_argument("--environment", default="local-dev", help="架构环境，例如 MCP Server / Cloud Worker / Tests")
    parser.add_argument("--phenomenon", required=True, help="错误信息/异常现象")
    parser.add_argument("--root-cause", required=True, help="根因分析")
    parser.add_argument("--steps", required=True, help="解决方案与步骤（可多行，用\\n）")
    parser.add_argument("--output-dir", default="lesson", help="输出目录（默认 lesson）")

    args = parser.parse_args()

    record = LessonRecord(
        title=args.title,
        module=args.module,
        environment=args.environment,
        phenomenon=args.phenomenon,
        root_cause=args.root_cause,
        solution_steps=args.steps.replace("\\n", "\n"),
    )

    path = write_lesson(record, output_dir=args.output_dir)
    sys.stdout.write(str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
