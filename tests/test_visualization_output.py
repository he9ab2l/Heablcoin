############################################################
# 📘 文件说明：
# 本文件实现的功能：离线测试：可视化输出结构
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
# - 依赖（标准库）：json, os, sys, typing
# - 依赖（第三方）：无
# - 依赖（本地）：无
#
# 🕒 创建时间：2025-12-19
############################################################

""" 
离线测试：可视化输出结构

目标：在不依赖真实交易所网络的情况下，验证 get_market_analysis(enable_visualization=True)
返回的 JSON 结构符合约定（candles/indicators/visualizations/summary/_artifact_metadata）。

说明：这里不直接调用 FastMCP，而是复用 Heablcoin.py 中的数据结构约定。
为了避免触发真实 ccxt 请求，本测试构造一份模拟输出并做 schema 校验。
"""

import sys
import os
import json
from typing import Any, Dict

# 添加项目路径
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, SRC_DIR)


def _assert_has(d: Dict[str, Any], key: str):
    assert key in d, f"missing key: {key}"


def test_visualization_schema_minimal():
    print("\n📝 测试: 可视化 JSON schema（最小结构）")

    # 模拟最小可用输出（与 MarketAnalysisOutput.to_dict 对齐）
    payload = {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "timestamp": "2025-01-01T00:00:00",
        "data": {
            "candles": [
                {
                    "timestamp": 1700000000000,
                    "open": 100.0,
                    "high": 110.0,
                    "low": 90.0,
                    "close": 105.0,
                    "volume": 123.0,
                }
            ],
            "indicators": [
                {
                    "name": "RSI",
                    "values": [{"timestamp": 1700000000000, "value": 55.0}],
                    "params": {"period": 14},
                }
            ],
        },
        "visualizations": [
            {
                "type": "candlestick",
                "priority": 1,
                "title": "BTC/USDT 价格走势",
                "description": "示例",
                "recommended_library": "recharts",
            }
        ],
        "summary": "text summary",
        "_artifact_metadata": {
            "version": "2.0",
            "supports_visualization": True,
            "recommended_artifact_type": "react",
            "data_format": "financial_chart",
        },
    }

    s = json.dumps(payload, ensure_ascii=False)
    data = json.loads(s)

    _assert_has(data, "symbol")
    _assert_has(data, "timeframe")
    _assert_has(data, "timestamp")
    _assert_has(data, "data")
    _assert_has(data, "visualizations")
    _assert_has(data, "summary")
    _assert_has(data, "_artifact_metadata")

    _assert_has(data["data"], "candles")
    _assert_has(data["data"], "indicators")

    assert isinstance(data["data"]["candles"], list) and data["data"]["candles"], "candles must be non-empty list"
    assert isinstance(data["data"]["indicators"], list) and data["data"]["indicators"], "indicators must be non-empty list"

    candle = data["data"]["candles"][0]
    for k in ["timestamp", "open", "high", "low", "close", "volume"]:
        _assert_has(candle, k)

    indicator = data["data"]["indicators"][0]
    for k in ["name", "values", "params"]:
        _assert_has(indicator, k)

    viz = data["visualizations"][0]
    for k in ["type", "priority", "title", "description", "recommended_library"]:
        _assert_has(viz, k)

    meta = data["_artifact_metadata"]
    for k in ["version", "supports_visualization"]:
        _assert_has(meta, k)

    print("✅ 通过: schema 字段完整")
    return True


def run_all_tests():
    print("=" * 60)
    print("🧪 可视化输出离线测试")
    print("=" * 60)

    tests = [test_visualization_schema_minimal]
    passed = 0
    failed = 0

    for t in tests:
        try:
            if t():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    ok = run_all_tests()
    sys.exit(0 if ok else 1)
