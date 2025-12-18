#!/usr/bin/env python3
############################################################
# 📘 文件说明：Add Headers
# 本文件实现的功能：add_headers 模块功能实现
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
# │  输入数据    │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  核心处理逻辑 │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  输出结果    │
# └──────────────┘
#
# 📊 数据管道说明：
# 数据流向：输入源 → 数据处理 → 核心算法 → 输出目标
#
# 🧩 文件结构：
# - 函数: get_relative_path, extract_imports, extract_classes_and_functions, generate_header, has_standard_header
#
# 🔗 主要依赖：argparse, ast, datetime, os, pathlib, re, typing
#
# 🕒 创建时间：2025-12-18
############################################################

"""
批量添加标准化头注释脚本
========================
为项目中所有Python文件添加规范的文件头注释
"""

import os
import re
import ast
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Set

# 排除的目录
EXCLUDED_DIRS = {
    'venv', '.venv', 'site-packages', '__pycache__', 
    '.git', 'node_modules', '.tox', 'dist', 'build', 'egg-info'
}

# 文件功能映射（基于文件名和路径推断）
FILE_DESCRIPTIONS = {
    # 根目录
    'Heablcoin.py': ('MCP Server 主入口', '智能加密货币量化交易系统的核心服务端，注册所有MCP工具，提供市场分析、交易执行、账户管理等功能'),
    'Heablcoin-test.py': ('终端综合测试入口', '无需MCP客户端即可对Heablcoin核心能力进行一键自检'),
    'qinglong_worker.py': ('青龙/云端监控Worker', '轮询Redis监控任务，满足条件时执行通知等动作'),
    
    # cloud 模块
    'cloud/__init__.py': ('云端模块初始化', '云端任务调度与API管理模块的包初始化'),
    'cloud/api_manager.py': ('云端API管理器', '多API提供商支持，含负载均衡、故障转移、速率限制'),
    'cloud/enhanced_publisher.py': ('增强任务发布器', '支持优先级队列、任务依赖、批量操作、任务过期'),
    'cloud/mcp_tools.py': ('云端MCP工具', '注册云端相关的MCP工具函数'),
    'cloud/pipeline_worker.py': ('流水线Worker', '处理AI流水线任务的工作进程'),
    'cloud/publisher.py': ('任务发布器', '基础的云端任务发布功能'),
    'cloud/scheduler.py': ('云端调度器', '轻量级服务端定时任务调度'),
    'cloud/task_executor.py': ('任务执行器', '从任务队列取任务执行并回填结果'),
    'cloud/task_manager.py': ('任务管理器', '将MCP侧监控任务写入Redis供云端Worker读取'),
    
    # data 模块
    'data/__init__.py': ('数据模块初始化', '数据管理模块的包初始化'),
    'data/manager.py': ('数据管理器', '统一的数据获取、缓存和持久化管理'),
    
    # learning 模块
    'learning/__init__.py': ('学习模块初始化', '交易学习与复盘模块的包初始化'),
    'learning/core.py': ('学习核心逻辑', '交易学习与复盘的核心功能实现'),
    'learning/discipline.py': ('交易纪律模块', '交易纪律检查与提醒功能'),
    'learning/mcp_tools.py': ('学习MCP工具', '注册学习模块的MCP工具函数'),
    'learning/notifier.py': ('学习通知器', '学习进度和复盘结果的通知功能'),
    'learning/registry.py': ('学习注册表', '学习模块的配置和功能注册'),
    'learning/storage.py': ('学习存储', '学习记录的持久化存储'),
    'learning/modules/__init__.py': ('学习子模块初始化', '学习子模块的包初始化'),
    'learning/modules/growth.py': ('成长分析模块', '交易者成长轨迹分析'),
    'learning/modules/history.py': ('历史分析模块', '历史交易数据分析'),
    'learning/modules/in_trade.py': ('交易中分析', '持仓期间的实时分析与提醒'),
    'learning/modules/pre_trade.py': ('交易前分析', '开仓前的检查与分析'),
    'learning/modules/utility.py': ('学习工具函数', '学习模块的通用工具函数'),
    
    # market_analysis 模块
    'market_analysis/__init__.py': ('市场分析初始化', '市场分析模块的包初始化'),
    'market_analysis/cache_manager.py': ('分析缓存管理', '市场分析结果的缓存管理'),
    'market_analysis/core.py': ('市场分析核心', '技术分析、情绪分析、信号生成的核心逻辑'),
    'market_analysis/data_provider.py': ('数据提供器', '市场数据的获取与预处理'),
    'market_analysis/mcp_tools.py': ('市场分析MCP工具', '注册市场分析相关的MCP工具'),
    'market_analysis/registry.py': ('分析注册表', '分析模块的配置和指标注册'),
    'market_analysis/report_generator.py': ('报告生成器', '生成市场分析报告'),
    'market_analysis/state_manager.py': ('状态管理器', '市场分析状态的管理'),
    'market_analysis/utils.py': ('分析工具函数', '市场分析的通用工具函数'),
    'market_analysis/indicators/__init__.py': ('指标模块初始化', '技术指标子模块的包初始化'),
    'market_analysis/indicators/momentum_indicators.py': ('动量指标', 'RSI、MACD、Stochastic等动量类指标'),
    'market_analysis/indicators/pipeline.py': ('指标流水线', '技术指标的批量计算流水线'),
    'market_analysis/indicators/trend_indicators.py': ('趋势指标', 'MA、EMA、ADX等趋势类指标'),
    'market_analysis/indicators/volatility_indicators.py': ('波动率指标', 'ATR、布林带等波动率指标'),
    'market_analysis/indicators/volume_indicators.py': ('成交量指标', 'OBV、VWAP等成交量指标'),
    'market_analysis/modules/__init__.py': ('分析子模块初始化', '市场分析子模块的包初始化'),
    'market_analysis/modules/fundamental.py': ('基本面分析', '加密货币基本面数据分析'),
    'market_analysis/modules/market_structure.py': ('市场结构分析', '支撑阻力、趋势结构分析'),
    'market_analysis/modules/patterns.py': ('形态识别', 'K线形态和图表形态识别'),
    'market_analysis/modules/sentiment.py': ('情绪分析', '市场情绪指标分析'),
    'market_analysis/modules/technical_summary.py': ('技术总结', '技术分析综合总结'),
    'market_analysis/modules/trading_signals.py': ('交易信号', '买卖信号生成与评估'),
    
    # orchestration 模块
    'orchestration/__init__.py': ('编排模块初始化', 'AI编排模块的包初始化'),
    'orchestration/ai_roles.py': ('AI角色定义', '定义不同AI角色的职责和提示词'),
    'orchestration/ai_router.py': ('AI路由器', 'AI请求的路由和分发'),
    'orchestration/mcp_tools.py': ('编排MCP工具', '注册编排相关的MCP工具'),
    'orchestration/providers.py': ('AI提供商', '多AI服务提供商的适配器'),
    'orchestration/router.py': ('任务路由器', '任务流的路由和编排'),
    'orchestration/tasks.py': ('任务定义', '标准任务类型和执行逻辑'),
    
    # personal_analytics 模块
    'personal_analytics/__init__.py': ('个人分析初始化', '个人绩效分析模块的包初始化'),
    'personal_analytics/core.py': ('个人分析核心', '账户盈亏、风险分析的核心逻辑'),
    'personal_analytics/data_provider.py': ('个人数据提供器', '交易历史和账户数据的获取'),
    'personal_analytics/mcp_tools.py': ('个人分析MCP工具', '注册个人分析相关的MCP工具'),
    'personal_analytics/modules/__init__.py': ('个人分析子模块初始化', '个人分析子模块的包初始化'),
    'personal_analytics/modules/attribution.py': ('归因分析', '交易盈亏归因分析'),
    'personal_analytics/modules/behavior.py': ('行为分析', '交易行为模式分析'),
    'personal_analytics/modules/cost_analysis.py': ('成本分析', '交易成本和费用分析'),
    'personal_analytics/modules/funds_flow.py': ('资金流分析', '资金流入流出分析'),
    'personal_analytics/modules/performance.py': ('绩效分析', '交易绩效指标计算'),
    'personal_analytics/modules/period_stats.py': ('周期统计', '按时间周期的交易统计'),
    'personal_analytics/modules/portfolio.py': ('组合分析', '投资组合分析'),
    'personal_analytics/modules/risk.py': ('风险分析', '风险暴露和风险指标'),
    'personal_analytics/modules/session_analysis.py': ('交易时段分析', '不同交易时段的表现分析'),
    'personal_analytics/modules/trade_journal.py': ('交易日志', '交易记录和日志管理'),
    'personal_analytics/modules/trading_behavior.py': ('交易行为', '详细交易行为分析'),
    
    # report 模块
    'report/__init__.py': ('报告模块初始化', '报告生成模块的包初始化'),
    'report/query_backup.py': ('查询备份', '报告查询的备份功能'),
    'report/flexible_report/__init__.py': ('灵活报告初始化', '灵活报告子模块的包初始化'),
    'report/flexible_report/analytics.py': ('报告分析', '报告数据分析功能'),
    'report/flexible_report/defaults.py': ('报告默认值', '报告的默认配置和模板'),
    'report/flexible_report/render.py': ('报告渲染', '报告的格式化和渲染'),
    'report/flexible_report/service.py': ('报告服务', '报告生成的核心服务'),
    'report/flexible_report/state.py': ('报告状态', '报告生成状态管理'),
    'report/flexible_report/storage.py': ('报告存储', '报告的持久化存储'),
    'report/flexible_report/trade_log.py': ('交易日志报告', '交易日志的报告生成'),
    'report/flexible_report/utils.py': ('报告工具函数', '报告模块的通用工具'),
    
    # storage 模块
    'storage/__init__.py': ('存储模块初始化', '多后端存储模块的包初始化'),
    'storage/base.py': ('存储基类', '存储适配器的抽象基类'),
    'storage/email_adapter.py': ('邮件存储适配器', '通过邮件发送存储内容'),
    'storage/file_adapter.py': ('文件存储适配器', '本地文件系统存储'),
    'storage/notion_adapter.py': ('Notion存储适配器', '同步到Notion数据库'),
    'storage/redis_adapter.py': ('Redis存储适配器', 'Redis缓存和队列操作'),
    
    # tests 模块
    'tests/__init__.py': ('测试模块初始化', '测试套件的包初始化'),
    'tests/run_tests.py': ('测试运行器', '统一的测试运行入口'),
    'tests/test_email_connection.py': ('邮件连接测试', '测试邮件服务配置'),
    'tests/test_integration_full.py': ('完整集成测试', '全功能集成测试'),
    'tests/test_integration_simple.py': ('简单集成测试', '快速集成测试'),
    'tests/test_learning.py': ('学习模块测试', '学习功能单元测试'),
    'tests/test_llm_router.py': ('LLM路由测试', 'AI路由功能测试'),
    'tests/test_mcp_tools.py': ('MCP工具测试', 'MCP工具函数测试'),
    'tests/test_smart_cache.py': ('智能缓存测试', '缓存功能测试'),
    'tests/test_smart_logger.py': ('智能日志测试', '日志功能测试'),
    'tests/test_upgrades_old.py': ('旧版升级测试', '版本升级兼容性测试'),
    'tests/test_visualization_output.py': ('可视化输出测试', '图表输出功能测试'),
    
    # utils 模块
    'utils/__init__.py': ('工具模块初始化', '通用工具模块的包初始化'),
    'utils/async_helper.py': ('异步工具', '异步操作辅助函数'),
    'utils/backtesting.py': ('回测引擎', '简单策略回测功能'),
    'utils/exchange_adapter.py': ('交易所适配器', '统一的多交易所接口'),
    'utils/notifier.py': ('通知工具', '多通道通知框架'),
    'utils/performance_monitor.py': ('性能监控', '函数性能监控和统计'),
    'utils/risk_management.py': ('风险管理', '仓位计算和追踪止损'),
    'utils/smart_cache.py': ('智能缓存', 'TTL缓存和装饰器'),
    'utils/smart_logger.py': ('智能日志', '多通道日志系统'),
    'utils/trade_storage.py': ('交易存储', '交易记录的本地存储'),
}


def get_relative_path(file_path: Path, base_path: Path) -> str:
    """获取相对路径"""
    try:
        return str(file_path.relative_to(base_path)).replace('\\', '/')
    except ValueError:
        return str(file_path)


def extract_imports(content: str) -> List[str]:
    """提取导入的模块"""
    imports = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split('.')[0])
    except:
        # 使用正则提取
        import_pattern = r'^(?:from\s+(\w+)|import\s+(\w+))'
        for match in re.finditer(import_pattern, content, re.MULTILINE):
            mod = match.group(1) or match.group(2)
            if mod:
                imports.append(mod)
    return sorted(set(imports))


def extract_classes_and_functions(content: str) -> Tuple[List[str], List[str]]:
    """提取类和函数名"""
    classes = []
    functions = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                if not node.name.startswith('_'):
                    functions.append(node.name)
    except:
        # 使用正则
        class_pattern = r'^class\s+(\w+)'
        func_pattern = r'^(?:async\s+)?def\s+(\w+)'
        for match in re.finditer(class_pattern, content, re.MULTILINE):
            classes.append(match.group(1))
        for match in re.finditer(func_pattern, content, re.MULTILINE):
            name = match.group(1)
            if not name.startswith('_'):
                functions.append(name)
    return classes[:5], functions[:8]  # 限制数量


def generate_header(file_path: Path, base_path: Path, content: str) -> str:
    """生成标准化头注释"""
    rel_path = get_relative_path(file_path, base_path)
    
    # 获取文件描述
    title, desc = FILE_DESCRIPTIONS.get(rel_path, ('', ''))
    if not title:
        # 根据文件名推断
        name = file_path.stem
        if name == '__init__':
            parent = file_path.parent.name
            title = f'{parent}模块初始化'
            desc = f'{parent}模块的包初始化文件'
        else:
            title = name.replace('_', ' ').title()
            desc = f'{name} 模块功能实现'
    
    # 提取信息
    imports = extract_imports(content)
    classes, functions = extract_classes_and_functions(content)
    
    # 构建模块列表
    modules = []
    if classes:
        modules.append(f"类: {', '.join(classes[:3])}")
    if functions:
        modules.append(f"函数: {', '.join(functions[:5])}")
    if not modules:
        modules = ["核心逻辑实现"]
    
    # 生成流程图（简化版）
    if 'mcp_tools' in rel_path:
        flow = """# ┌──────────────┐
# │  MCP 请求    │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  工具函数处理 │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  返回结果    │
# └──────────────┘"""
    elif 'test' in rel_path.lower():
        flow = """# ┌──────────────┐
# │  测试用例    │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  执行断言    │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  输出结果    │
# └──────────────┘"""
    elif '__init__' in rel_path:
        flow = """# ┌──────────────┐
# │  模块导入    │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  导出接口    │
# └──────────────┘"""
    else:
        flow = """# ┌──────────────┐
# │  输入数据    │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  核心处理逻辑 │
# └──────┬───────┘
#        ↓
# ┌──────────────┐
# │  输出结果    │
# └──────────────┘"""
    
    # 数据管道
    if 'storage' in rel_path or 'adapter' in rel_path:
        pipeline = "数据流向：应用层 → 存储适配器 → 外部存储（文件/Redis/Notion/邮件）"
    elif 'analysis' in rel_path:
        pipeline = "数据流向：交易所API → 数据处理 → 指标计算 → 分析结果输出"
    elif 'cloud' in rel_path:
        pipeline = "数据流向：MCP请求 → 任务队列 → 云端执行 → 结果回调"
    else:
        pipeline = "数据流向：输入源 → 数据处理 → 核心算法 → 输出目标"
    
    # 当前日期
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    header = f'''############################################################
# 📘 文件说明：{title}
# 本文件实现的功能：{desc}
#
# 📋 程序整体伪代码（中文）：
# 1. 初始化依赖模块和配置
# 2. 定义核心类和函数
# 3. 实现主要业务逻辑
# 4. 提供对外接口
# 5. 异常处理与日志记录
#
# 🔄 程序流程图（逻辑流）：
{flow}
#
# 📊 数据管道说明：
# {pipeline}
#
# 🧩 文件结构：
# - {chr(10).join(["# - " + m for m in modules])[4:]}
#
# 🔗 主要依赖：{", ".join(imports[:8]) if imports else "无外部依赖"}
#
# 🕒 创建时间：{date_str}
############################################################
'''
    return header


def has_standard_header(content: str) -> bool:
    """检查是否已有标准头注释"""
    return '############################################################' in content[:500] and '📘 文件说明' in content[:1000]


def process_file(file_path: Path, base_path: Path, dry_run: bool = False) -> bool:
    """处理单个文件"""
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"❌ 读取失败: {file_path} - {e}")
        return False
    
    # 检查是否已有头注释
    if has_standard_header(content):
        print(f"⏭️  跳过（已有头注释）: {file_path}")
        return True
    
    # 保留 shebang 和 encoding 声明
    lines = content.split('\n')
    preserved_lines = []
    start_idx = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('#!') or (stripped.startswith('#') and 'coding' in stripped):
            preserved_lines.append(line)
            start_idx = i + 1
        elif stripped.startswith('# -*-') and 'coding' in stripped:
            preserved_lines.append(line)
            start_idx = i + 1
        else:
            break
    
    # 跳过现有的简单docstring（保留内容，添加在头注释后）
    remaining_content = '\n'.join(lines[start_idx:])
    
    # 生成头注释
    header = generate_header(file_path, base_path, content)
    
    # 组合新内容
    if preserved_lines:
        new_content = '\n'.join(preserved_lines) + '\n' + header + '\n' + remaining_content
    else:
        new_content = header + '\n' + remaining_content
    
    if dry_run:
        print(f"🔍 预览: {file_path}")
        print(header[:500] + "...")
        return True
    
    try:
        file_path.write_text(new_content, encoding='utf-8')
        print(f"✅ 已更新: {file_path}")
        return True
    except Exception as e:
        print(f"❌ 写入失败: {file_path} - {e}")
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description='批量添加标准化头注释')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际修改文件')
    parser.add_argument('--path', default='.', help='项目根目录')
    args = parser.parse_args()
    
    base_path = Path(args.path).resolve()
    print(f"📂 扫描目录: {base_path}")
    
    # 收集所有Python文件
    py_files = []
    for root, dirs, files in os.walk(base_path):
        # 排除特定目录
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith('.')]
        
        for f in files:
            if f.endswith('.py'):
                py_files.append(Path(root) / f)
    
    print(f"📝 找到 {len(py_files)} 个Python文件")
    
    success = 0
    failed = 0
    
    for file_path in sorted(py_files):
        if process_file(file_path, base_path, args.dry_run):
            success += 1
        else:
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"✅ 成功: {success}")
    print(f"❌ 失败: {failed}")
    print(f"📊 总计: {len(py_files)}")


if __name__ == '__main__':
    main()
