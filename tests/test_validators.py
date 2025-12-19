############################################################
# 📘 文件说明：
# 本文件实现的功能：测试用例：验证 test_validators 相关逻辑的正确性与回归。
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
# - 依赖（标准库）：os, sys
# - 依赖（第三方）：无
# - 依赖（本地）：utils.validators
#
# 🕒 创建时间：2025-12-19
############################################################

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, SRC_DIR)

from utils.validators import (
    parse_price,
    validate_price_condition,
    is_valid_wallet_address,
    normalize_symbol,
)


def test_parse_price():
    assert parse_price("123.45") == 123.45
    assert parse_price(10) == 10.0
    assert parse_price("12_345") == 12345.0
    try:
        parse_price("-1", min_value=0)
    except ValueError:
        return
    raise AssertionError("negative price should fail")


def test_validate_condition():
    assert validate_price_condition("price < 50000") == 50000.0
    try:
        validate_price_condition("volume > 10")
    except ValueError:
        return
    raise AssertionError("invalid condition must raise")


def test_wallet_addresses():
    assert is_valid_wallet_address("0x" + "a" * 40)
    assert not is_valid_wallet_address("0x123")
    assert is_valid_wallet_address("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080", "btc")


def test_normalize_symbol():
    assert normalize_symbol("eth\\usdt") == "ETH/USDT"
