"""
Heablcoin MCP Server
====================
智能加密货币量化交易系统
支持：AI决策分析、自动交易、技术分析、账户管理、邮件推送、详细日志
"""

import os
import sys
import asyncio
import warnings
import json

# === CRITICAL: MCP Protocol Protection ===
# MCP通过stdout传输JSON-RPC消息，任何print()或第三方库输出都会污染协议通道
# 将stdout重定向到stderr，防止污染JSON-RPC通道
_original_stdout = sys.stdout
sys.stdout = sys.stderr

# --- 0. 环境初始化 ---
warnings.simplefilter("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import time
import csv
import threading
import logging
from logging.handlers import RotatingFileHandler
import smtplib
import ccxt
import pandas as pd
import numpy as np
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime, timedelta
from pathlib import Path
import re
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from typing import Any, Optional, Dict, List, Callable
import html
import functools
import traceback
from dataclasses import dataclass, asdict

from report.flexible_report.service import register_tools as _register_flexible_report_tools
from market_analysis.mcp_tools import register_tools as _register_market_analysis_tools
from personal_analytics.mcp_tools import register_tools as _register_personal_analytics_tools
from learning.mcp_tools import register_tools as _register_learning_tools
from orchestration.mcp_tools import register_tools as _register_orchestration_tools
from cloud.mcp_tools import register_tools as _register_cloud_tools

try:
    import markdown as _markdown
except Exception:
    _markdown = None

################################
# --- P0-2: 全局异常捕获装饰器 ---
################################

DEBUG_MODE = False

def mcp_tool_safe(func: Callable) -> Callable:
    """
    MCP工具安全装饰器
    - 捕获所有异常，防止MCP Server崩溃
    - 返回友好的错误信息给用户
    - 记录完整堆栈到日志供调试
    - 保持MCP连接不断开
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 记录详细错误（供调试）
            error_detail = {
                "tool": func.__name__,
                "error_type": type(e).__name__,
                "error_msg": str(e),
                "traceback": traceback.format_exc()
            }
            
            # 使用logging记录（此时logger可能还未初始化，所以用print到stderr作为后备）
            try:
                logging.error(f"❌ MCP Tool Error [{func.__name__}]: {error_detail}")
            except:
                print(f"❌ MCP Tool Error [{func.__name__}]: {error_detail}", file=sys.stderr)
            
            # 返回用户友好的错误信息
            error_msg = f"""⚠️ 工具执行失败

**错误类型**: {type(e).__name__}
**错误信息**: {str(e)}

**建议**:
- 检查参数是否正确
- 查看日志文件获取详细信息
- 稍后重试

_工具: {func.__name__}_"""
            
            if DEBUG_MODE:
                error_msg += f"\n\n**调试信息**:\n```\n{error_detail['traceback']}\n```"
            
            return error_msg
    
    return wrapper


################################
# --- 配置 ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 加载环境变量
load_dotenv(os.path.join(CURRENT_DIR, '.env'))

def _env_str(name: str, default: str) -> str:
    v = os.getenv(name)
    if v is None:
        return default
    v = v.strip()
    return v if v else default


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if not v:
        return default
    try:
        return int(v)
    except ValueError:
        return default


def _env_bool(name: str, default: bool = True) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {'1', 'true', 'yes', 'y', 'on'}


def _env_float(name: str, default: float) -> float:
    v = os.getenv(name)
    if not v:
        return default
    try:
        return float(v)
    except ValueError:
        return default


def _resolve_path(p: str, default_rel: str) -> str:
    p = (p or '').strip()
    if not p:
        p = default_rel
    if os.path.isabs(p):
        return p
    return os.path.join(CURRENT_DIR, p)


LOG_FILE = _resolve_path(_env_str('LOG_FILE', os.path.join('logs', 'server_debug.log')), os.path.join('logs', 'server_debug.log'))
TRADE_LOG_FILE = os.path.join(CURRENT_DIR, 'trade_history.csv')
TRADE_DB_FILE = _resolve_path(_env_str('TRADE_DB_FILE', os.path.join('data', 'trades.db')), os.path.join('data', 'trades.db'))
ALERT_LOG_FILE = os.path.join(CURRENT_DIR, 'price_alerts.json')
REPORTS_DIR = os.path.join(CURRENT_DIR, 'reports', 'analysis_reports')

LOG_DIR = _resolve_path(_env_str('LOG_DIR', 'logs'), 'logs')

LOG_ROTATE_MAX_BYTES = _env_int('LOG_ROTATE_MAX_BYTES', 5 * 1024 * 1024)
LOG_ROTATE_BACKUP_COUNT = _env_int('LOG_ROTATE_BACKUP_COUNT', 3)

PERF_SLOW_THRESHOLD_SECONDS = _env_float('PERF_SLOW_THRESHOLD_SECONDS', 3.0)
PERF_DEGRADATION_FACTOR = _env_float('PERF_DEGRADATION_FACTOR', 2.0)
PERF_DEGRADATION_MIN_CALLS = _env_int('PERF_DEGRADATION_MIN_CALLS', 10)

CACHE_DEFAULT_TTL_SECONDS = _env_int('CACHE_DEFAULT_TTL_SECONDS', 300)

EXCHANGE_POOL_TTL_SECONDS = _env_int('EXCHANGE_POOL_TTL_SECONDS', 60)

CCXT_TIMEOUT_MS = _env_int('CCXT_TIMEOUT_MS', 30000)
CCXT_ENABLE_RATE_LIMIT = _env_bool('CCXT_ENABLE_RATE_LIMIT', True)
CCXT_DEFAULT_TYPE = _env_str('CCXT_DEFAULT_TYPE', 'spot')
CCXT_RECV_WINDOW = _env_int('CCXT_RECV_WINDOW', 10000)
CCXT_ADJUST_TIME_DIFFERENCE = _env_bool('CCXT_ADJUST_TIME_DIFFERENCE', False)

OHLCV_LIMIT_MARKET_ANALYSIS = _env_int('OHLCV_LIMIT_MARKET_ANALYSIS', 100)
OHLCV_LIMIT_COMPREHENSIVE_ANALYSIS = _env_int('OHLCV_LIMIT_COMPREHENSIVE_ANALYSIS', 100)
OHLCV_LIMIT_SENTIMENT = _env_int('OHLCV_LIMIT_SENTIMENT', 100)
OHLCV_LIMIT_OVERVIEW = _env_int('OHLCV_LIMIT_OVERVIEW', 20)
OHLCV_LIMIT_MARKET_OVERVIEW = _env_int('OHLCV_LIMIT_MARKET_OVERVIEW', 50)
OHLCV_LIMIT_SIGNALS = _env_int('OHLCV_LIMIT_SIGNALS', 100)
OHLCV_LIMIT_STRATEGY = _env_int('OHLCV_LIMIT_STRATEGY', 60)

DEBUG_MODE = _env_bool('DEBUG_MODE', False)

Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

# --- P1: 交易记录 SQLite 存储（兼容模式：CSV 仍保留作备份） ---
ENABLE_TRADE_DB = _env_bool('ENABLE_TRADE_DB', True)
try:
    if not ENABLE_TRADE_DB:
        raise RuntimeError('disabled by ENABLE_TRADE_DB')
    from utils.trade_storage import TradeStore
    trade_store = TradeStore(db_path=TRADE_DB_FILE, csv_path=TRADE_LOG_FILE)
    USE_TRADE_DB = True
except Exception as e:
    print(f"⚠️ TradeStore加载失败，使用CSV存储: {e}", file=sys.stderr)
    trade_store = None
    USE_TRADE_DB = False

_TRADE_CSV_LOCK = threading.RLock()

def _parse_symbols(value: str) -> set:
    parts = [p.strip() for p in (value or '').split(',')]
    return {p for p in parts if p}


def _get_allowed_symbols() -> set:
    default = 'BTC/USDT,ETH/USDT,BNB/USDT,ADA/USDT,XRP/USDT,SOL/USDT,DOT/USDT,DOGE/USDT,AVAX/USDT,LINK/USDT,MATIC/USDT,UNI/USDT,ATOM/USDT,LTC/USDT,ETC/USDT'
    return _parse_symbols(os.getenv('ALLOWED_SYMBOLS', default))


def _get_max_trade_amount() -> float:
    return _env_float('MAX_TRADE_AMOUNT', 1000.0)


def _get_daily_trade_limit() -> float:
    return _env_float('DAILY_TRADE_LIMIT', 5000.0)


# 通知开关（默认 True；可通过 MCP 工具在运行时覆盖）
_NOTIFY_RUNTIME_OVERRIDES: Dict[str, Optional[bool]] = {
    'NOTIFY_TRADE_EXECUTION': None,
    'NOTIFY_PRICE_ALERTS': None,
    'NOTIFY_DAILY_REPORT': None,
    'NOTIFY_SYSTEM_ERRORS': None,
}


def _notify_enabled(key: str, default: bool = True) -> bool:
    override = _NOTIFY_RUNTIME_OVERRIDES.get(key)
    if override is not None:
        return bool(override)
    return _env_bool(key, default)


def _notify_switch_for_msg_type(msg_type: str) -> bool:
    msg_type = (msg_type or '').upper().strip()
    mapping = {
        'TRADE_EXECUTION': 'NOTIFY_TRADE_EXECUTION',
        'PRICE_ALERTS': 'NOTIFY_PRICE_ALERTS',
        'DAILY_REPORT': 'NOTIFY_DAILY_REPORT',
        'SYSTEM_ERRORS': 'NOTIFY_SYSTEM_ERRORS',
        'CUSTOM': None,
        'REPORT': 'NOTIFY_DAILY_REPORT',
    }
    key = mapping.get(msg_type)
    if key is None:
        return True
    return _notify_enabled(key, True)

# --- P0-3: 智能日志系统 ---
# 导入智能日志系统
ENABLE_SMART_LOGGER = _env_bool('ENABLE_SMART_LOGGER', True)
try:
    if not ENABLE_SMART_LOGGER:
        raise RuntimeError('disabled by ENABLE_SMART_LOGGER')
    from utils.smart_logger import get_smart_logger, log_performance
    smart_logger = get_smart_logger(
        base_dir=LOG_DIR,
        slow_threshold_seconds=PERF_SLOW_THRESHOLD_SECONDS,
        degradation_factor=PERF_DEGRADATION_FACTOR,
        degradation_min_calls=PERF_DEGRADATION_MIN_CALLS,
    )
    USE_SMART_LOGGER = True
except Exception as e:
    print(f"⚠️ SmartLogger加载失败，使用传统日志: {e}", file=sys.stderr)
    USE_SMART_LOGGER = False
    smart_logger = None

# --- P1-1: 智能缓存系统 ---
ENABLE_SMART_CACHE = _env_bool('ENABLE_SMART_CACHE', True)
try:
    if not ENABLE_SMART_CACHE:
        raise RuntimeError('disabled by ENABLE_SMART_CACHE')
    from utils.smart_cache import get_smart_cache, cached
    smart_cache = get_smart_cache()
    USE_SMART_CACHE = True
except Exception as e:
    print(f"⚠️ SmartCache加载失败，缓存功能禁用: {e}", file=sys.stderr)
    USE_SMART_CACHE = False
    smart_cache = None
    # 提供一个空装饰器作为后备
    def cached(ttl=300, key_prefix=""):
        def decorator(func):
            return func
        return decorator

# 传统日志系统（兼容模式）
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

_log_level_name = os.getenv('LOG_LEVEL', 'INFO').upper().strip()
_log_level = getattr(logging, _log_level_name, logging.INFO)

_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

_file_handler = RotatingFileHandler(LOG_FILE, maxBytes=LOG_ROTATE_MAX_BYTES, backupCount=LOG_ROTATE_BACKUP_COUNT, encoding='utf-8')
_file_handler.setLevel(_log_level)
_file_handler.setFormatter(_formatter)

_console_handler = logging.StreamHandler(sys.stderr)
_console_handler.setLevel(_log_level)
_console_handler.setFormatter(_formatter)

root_logger.setLevel(_log_level)
root_logger.addHandler(_file_handler)
root_logger.addHandler(_console_handler)

# 主logger（用于系统级日志）
if USE_SMART_LOGGER:
    logger = smart_logger.get_logger('system')
else:
    logger = logging.getLogger(__name__)
    logger.propagate = False

logger.info("=" * 50)
logger.info("🚀 Heablcoin MCP Server 启动")
logger.info(f"📁 工作目录: {CURRENT_DIR}")
if USE_SMART_LOGGER:
    logger.info("✅ 智能日志系统已启用（多通道 + 性能监控）")
if USE_SMART_CACHE:
    logger.info("✅ 智能缓存系统已启用（TTL缓存 + 统计）")

if not os.getenv("BINANCE_API_KEY"):
    logger.error("❌ 未找到 BINANCE_API_KEY")
else:
    logger.info("✅ 环境变量加载成功")

# 初始化 MCP Server
mcp = FastMCP("Heablcoin")

try:
    _register_market_analysis_tools(mcp)
except Exception as _e:
    logger.warning(f"⚠️ market_analysis 工具注册失败: {type(_e).__name__}: {_e}")

try:
    _register_personal_analytics_tools(mcp)
except Exception as _e:
    logger.warning(f"⚠️ personal_analytics 工具注册失败: {type(_e).__name__}: {_e}")

try:
    _register_learning_tools(mcp)
except Exception as _e:
    logger.warning(f"⚠️ learning 工具注册失败: {type(_e).__name__}: {_e}")

try:
    _register_orchestration_tools(mcp)
except Exception as _e:
    logger.warning(f"⚠️ orchestration 工具注册失败: {type(_e).__name__}: {_e}")

try:
    _register_cloud_tools(mcp)
except Exception as _e:
    logger.warning(f"⚠️ cloud 工具注册失败: {type(_e).__name__}: {_e}")

# ============================================
# 1. 基础设施层
# ============================================

class ExchangePool:
    """交易所连接池（单例模式）"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.exchange = None
            cls._instance.last_used = 0
        return cls._instance
    
    def get_exchange(self):
        current_time = time.time()
        if self.exchange and current_time - self.last_used < EXCHANGE_POOL_TTL_SECONDS:
            self.last_used = current_time
            return self.exchange
        
        api_key = os.getenv("BINANCE_API_KEY")
        secret = os.getenv("BINANCE_SECRET_KEY")
        use_testnet = os.getenv("USE_TESTNET", "True").lower() == "true"

        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': CCXT_ENABLE_RATE_LIMIT,
            'timeout': CCXT_TIMEOUT_MS,
            'options': {
                'defaultType': CCXT_DEFAULT_TYPE,
                'adjustForTimeDifference': CCXT_ADJUST_TIME_DIFFERENCE,
                'recvWindow': CCXT_RECV_WINDOW
            }
        })

        if use_testnet:
            self.exchange.set_sandbox_mode(True)
            logger.info("📡 已连接 Binance Testnet")
        else:
            logger.info("📡 已连接 Binance 主网")
        
        self.last_used = current_time
        return self.exchange

def get_exchange():
    return ExchangePool().get_exchange()


def _safe_filename_component(value: str) -> str:
    value = (value or '').strip()
    value = value.replace('/', '_').replace('\\', '_')
    value = re.sub(r'[^A-Za-z0-9._-]+', '_', value)
    value = re.sub(r'_+', '_', value).strip('_')
    return value or 'unknown'


def _ensure_reports_dir(date_str: str) -> str:
    base = Path(REPORTS_DIR)
    out_dir = base / date_str
    out_dir.mkdir(parents=True, exist_ok=True)
    return str(out_dir)


def _write_text(path: str, content: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)


def _write_json(path: str, data: Dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================
# 2. 通知系统
# ============================================

_EMAIL_GITHUB_STYLE = """
body { margin: 0; padding: 0; background: #f6f8fa; }
.container { max-width: 920px; margin: 0 auto; padding: 16px; }
.card { background: #ffffff; border: 1px solid #d0d7de; border-radius: 10px; overflow: hidden; }
.header { padding: 16px 18px; border-bottom: 1px solid #d0d7de; background: #f6f8fa; }
.header h1 { margin: 0; font-size: 18px; font-weight: 700; color: #24292f; }
.meta { margin-top: 6px; font-size: 12px; color: #57606a; }
.content { padding: 18px; }
.markdown-body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; color: #24292f; font-size: 14px; line-height: 1.6; }
.markdown-body h1, .markdown-body h2, .markdown-body h3 { border-bottom: 1px solid #d0d7de; padding-bottom: 0.3em; }
.markdown-body code { background: rgba(175,184,193,0.2); padding: .2em .4em; border-radius: 6px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, 'Liberation Mono', 'Courier New', monospace; }
.markdown-body pre { background: #f6f8fa; padding: 12px; border-radius: 10px; overflow: auto; border: 1px solid #d0d7de; }
.markdown-body pre code { background: transparent; padding: 0; }
.markdown-body table { border-collapse: collapse; width: 100%; }
.markdown-body th, .markdown-body td { border: 1px solid #d0d7de; padding: 8px 10px; }
.footer { padding: 12px 18px; border-top: 1px solid #d0d7de; background: #f6f8fa; font-size: 12px; color: #57606a; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 999px; border: 1px solid #d0d7de; background: #ffffff; font-size: 12px; color: #24292f; }
@media (max-width: 600px) { .container { padding: 10px; } .content { padding: 14px; } }
""".strip()


def _looks_like_html(text: str) -> bool:
    t = (text or '').lstrip().lower()
    return t.startswith('<!doctype') or t.startswith('<html') or ('<body' in t and '</' in t)


def _render_markdown(text: str, title: str) -> str:
    """将 Markdown 渲染为带 UTF-8 meta 的美观 HTML（类 GitHub Readme 风格）。

    若 markdown 依赖不存在，则自动降级为 <pre> 纯文本。
    """
    safe_title = html.escape(str(title or '').strip() or 'Heablcoin')
    raw = str(text or '')

    if _looks_like_html(raw):
        # 避免嵌套 <html> / <body> 导致邮件客户端渲染异常：只取 body 内部内容
        m = re.search(r'<body[^>]*>([\s\S]*?)</body>', raw, flags=re.IGNORECASE)
        if m:
            body = m.group(1)
        else:
            # 兜底：粗暴去掉最外层 html/body 标签
            body = re.sub(r'</?(html|body)[^>]*>', '', raw, flags=re.IGNORECASE).strip()
    else:
        if _markdown is None:
            body = f"<pre>{html.escape(raw)}</pre>"
        else:
            rendered = _markdown.markdown(
                raw,
                extensions=['fenced_code', 'tables', 'sane_lists', 'nl2br'],
                output_format='html5',
            )
            body = rendered

    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    doc = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <style>{_EMAIL_GITHUB_STYLE}</style>
</head>
<body>
  <div class="container">
    <div class="card">
      <div class="header">
        <h1>{safe_title}</h1>
        <div class="meta">发送时间：{created_at} <span class="badge">Heablcoin</span></div>
      </div>
      <div class="content">
        <div class="markdown-body">{body}</div>
      </div>
      <div class="footer">🤖 Heablcoin 智能交易系统自动发送（请勿直接回复此邮件）</div>
    </div>
  </div>
</body>
</html>"""
    return doc


def send_email(subject: str, html_content: str, msg_type: str = 'CUSTOM') -> bool:
    """发送邮件通知。

    - 输入优先视为 Markdown，并渲染为 HTML（带 <meta charset="utf-8">，解决中文乱码）
    - 若检测到输入本身就是 HTML，则直接包装为邮件 HTML
    - Windows 下部分 SMTP 实现会在发送成功后抛出 (-1, b'\x00\x00\x00') / Remote end closed
      这里会按“可能已发送”处理：记录 Warning 并返回 True。
    """
    try:
        if not _notify_switch_for_msg_type(msg_type):
            logger.debug(f"📧 已按通知开关屏蔽发送: msg_type={msg_type}")
            return False
        if os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "False").lower() != "true":
            logger.debug("📧 邮件通知未启用")
            return False

        sender = os.getenv("SENDER_EMAIL") or os.getenv("SMTP_USER")
        password = os.getenv("SENDER_PASSWORD") or os.getenv("SMTP_PASS")
        receiver = (
            os.getenv("RECIPIENT_EMAIL")
            or os.getenv("RECEIVER_EMAIL")
            or os.getenv("NOTIFY_EMAIL")
            or sender
        )
        smtp_server = os.getenv("SMTP_SERVER", "smtp.qq.com")
        smtp_port = int(os.getenv("SMTP_PORT", "465"))

        if not all([sender, password, receiver]):
            logger.warning("⚠️ 邮箱配置不完整")
            return False

        safe_subject = str(subject or '').strip() or 'Heablcoin Notification'
        raw_content = str(html_content or '')

        # 1) HTML 渲染
        body_html = _render_markdown(raw_content, safe_subject)

        # 2) 纯文本回退（避免部分客户端不渲染 HTML）
        plain_fallback = re.sub(r'<[^>]+>', '', body_html)
        plain_fallback = re.sub(r'\n{3,}', '\n\n', plain_fallback).strip() or safe_subject

        msg = MIMEMultipart('alternative')
        msg['From'] = sender
        msg['To'] = receiver
        msg['Subject'] = str(Header(safe_subject, 'utf-8'))
        msg.attach(MIMEText(plain_fallback, 'plain', 'utf-8'))
        msg.attach(MIMEText(body_html, 'html', 'utf-8'))

        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30) as server:
                server.login(sender, password)
                result = server.send_message(msg)
                if result:
                    logger.warning(f"⚠️ 邮件发送部分失败: {result}")
                    return False
        else:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                server.starttls()
                server.login(sender, password)
                result = server.send_message(msg)
                if result:
                    logger.warning(f"⚠️ 邮件发送部分失败: {result}")
                    return False

        logger.info(f"📧 邮件发送成功: {safe_subject}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"❌ SMTP 认证失败: {e} (请检查邮箱账号和授权码)")
        return False
    except Exception as e:
        # Windows 常见假报错：发送成功后对端先断开
        err_text = str(e)
        if (
            '(-1' in err_text
            or 'Remote end closed' in err_text
            or 'Remote end closed connection' in err_text
        ):
            logger.warning(f"⚠️ 邮件可能已发送（Windows 假报错已忽略）: {type(e).__name__}: {e}")
            return True
        logger.error(f"❌ 邮件发送异常: {type(e).__name__}: {e}")
        return False


def _flex_account_snapshot() -> Dict[str, Any]:
    try:
        exchange = get_exchange()
        balance = exchange.fetch_balance()
        usdt_total = float(balance.get('total', {}).get('USDT', 0) or 0)
        usdt_free = float(balance.get('free', {}).get('USDT', 0) or 0)

        coins = []
        for coin, amount in (balance.get('total') or {}).items():
            try:
                amt = float(amount or 0)
            except Exception:
                continue
            if amt > 0 and coin not in {'USDT', 'BUSD', 'USDC'}:
                coins.append(coin)

        tickers = {}
        if coins:
            try:
                tickers = exchange.fetch_tickers()
            except Exception:
                tickers = {}

        holdings = []
        total_equity = usdt_total
        for coin in coins:
            sym = f"{coin}/USDT"
            last = None
            chg = 0.0
            if sym in tickers:
                last = tickers[sym].get('last')
                chg = tickers[sym].get('percentage') or 0.0
            if last is None:
                try:
                    t = exchange.fetch_ticker(sym)
                    last = t.get('last')
                    chg = t.get('percentage') or 0.0
                except Exception:
                    last = None
            if last is None:
                continue

            amt = float(balance.get('total', {}).get(coin, 0) or 0)
            value = amt * float(last)
            if value <= 1:
                continue
            total_equity += value
            holdings.append({
                'asset': coin,
                'qty': amt,
                'value': value,
                'change_pct': float(chg),
            })

        holdings.sort(key=lambda x: float(x.get('value', 0) or 0), reverse=True)
        return {
            'total_equity': total_equity,
            'available_usdt': usdt_free,
            'holdings': holdings,
        }
    except Exception:
        return {'total_equity': 0.0, 'available_usdt': 0.0, 'holdings': []}


def _flex_ai_decision(symbol: str = "BTC/USDT", mode: str = "simple") -> Dict[str, Any]:
    text = get_ai_trading_advice(symbol, mode)
    # 以原工具为准：邮件版只做轻量结构化，尽量从文本里抽取关键字段；抽取失败则原样透传
    data: Dict[str, Any] = {
        'advice': 'HOLD',
        'confidence': 0,
        'rsi': '',
        'macd': '',
        'support': '',
        'resistance': '',
        '_raw': text,
    }
    try:
        m = re.search(r"建议操作\*\*[:：]\s*([^\n]+)", text)
        if m:
            data['advice'] = m.group(1).strip()
        m = re.search(r"信心指数\*\*[:：].*?\((\d+)%\)", text)
        if m:
            data['confidence'] = float(m.group(1))
    except Exception:
        pass
    return data


def _flex_market_sentiment(symbol: str = "BTC/USDT") -> Dict[str, Any]:
    text = get_market_sentiment(symbol)
    data: Dict[str, Any] = {
        'fear_greed': 50,
        'label': '中性',
        'trend': '震荡',
        '_raw': text,
        'top_gainers': [],
        'top_losers': [],
    }
    try:
        m = re.search(r"评分\*\*[:：]\s*(\d+)\/100", text)
        if m:
            data['fear_greed'] = float(m.group(1))
    except Exception:
        pass
    return data


def _flex_open_orders(symbol: str = None) -> Dict[str, Any]:
    try:
        exchange = get_exchange()
        if symbol:
            orders = exchange.fetch_open_orders(symbol)
        else:
            if 'warnOnFetchOpenOrdersWithoutSymbol' not in exchange.options:
                exchange.options['warnOnFetchOpenOrdersWithoutSymbol'] = False
            orders = []
            for sym in sorted(_get_allowed_symbols()):
                try:
                    orders.extend(exchange.fetch_open_orders(sym))
                except Exception:
                    continue
        out = []
        for o in orders:
            out.append({
                'symbol': o.get('symbol'),
                'side': str(o.get('side') or '').upper(),
                'price': o.get('price') or 0,
                'qty': o.get('amount') or 0,
                'distance_pct': 0,
            })
        return {'orders': out}
    except Exception:
        return {'orders': []}


try:
    _register_flexible_report_tools(
        mcp,
        send_email_fn=send_email,
        notify_switch_fn=_notify_switch_for_msg_type,
        data_providers={
            "account_snapshot": lambda: _flex_account_snapshot(),
            "ai_decision": lambda symbol="BTC/USDT", mode="simple": _flex_ai_decision(symbol=symbol, mode=mode),
            "market_sentiment": lambda symbol="BTC/USDT": _flex_market_sentiment(symbol=symbol),
            "open_orders": lambda symbol=None: _flex_open_orders(symbol=symbol),
        },
    )
except Exception as _e:
    logger.warning(f"⚠️ send_flexible_report 注册失败: {type(_e).__name__}: {_e}")

@mcp.tool()
@mcp_tool_safe
def send_notification(title: str, message: str) -> str:
    """
    发送自定义邮件通知。
    Args:
        title: 邮件标题
        message: 邮件内容
    """
    html = f"<html><body><h2>{title}</h2><p>{message}</p><hr><small>🤖 Heablcoin 智能交易系统</small></body></html>"
    if send_email(title, html, msg_type='CUSTOM'):
        return f"✅ 通知已发送: {title}"
    return "❌ 发送失败，请检查邮箱配置"

def send_trade_notification(order_id, symbol, side, amount, price, cost, status):
    """交易完成后自动发送通知"""
    use_testnet = os.getenv("USE_TESTNET", "True").lower() == "true"
    env = "🧪 测试网" if use_testnet else "🔴 主网"
    emoji = "📈" if side.upper() == "BUY" else "📉"
    
    html = f"""
    <html><body style="font-family: Arial; padding: 20px;">
        <h2 style="color: #2c3e50;">{emoji} 交易执行通知</h2>
        <table style="border-collapse: collapse; width: 100%;">
            <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><b>时间</b></td><td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><b>交易对</b></td><td style="font-weight: bold; color: #3498db;">{symbol}</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><b>方向</b></td><td style="color: {'#27ae60' if side.upper()=='BUY' else '#e74c3c'}; font-weight: bold;">{side.upper()}</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><b>数量</b></td><td>{amount}</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><b>价格</b></td><td>${price:,.2f}</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><b>总额</b></td><td style="font-weight: bold;">{cost} USDT</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><b>订单ID</b></td><td style="font-family: monospace;">{order_id}</td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><b>状态</b></td><td>{status}</td></tr>
            <tr><td style="padding: 8px;"><b>环境</b></td><td>{env}</td></tr>
        </table>
        <p style="color: #7f8c8d; margin-top: 20px; font-size: 12px;">🤖 由 Heablcoin 智能交易系统自动发送（请勿直接回复此邮件）</p>
    </body></html>
    """
    send_email(f"{emoji} {symbol} {side.upper()} 交易通知", html, msg_type='TRADE_EXECUTION')


@mcp.tool()
@mcp_tool_safe
def get_notification_settings() -> str:
    """获取当前通知开关设置（包含 env 默认值与运行时覆盖值）。"""
    keys = [
        'NOTIFY_TRADE_EXECUTION',
        'NOTIFY_PRICE_ALERTS',
        'NOTIFY_DAILY_REPORT',
        'NOTIFY_SYSTEM_ERRORS',
    ]
    data = {
        'EMAIL_NOTIFICATIONS_ENABLED': os.getenv('EMAIL_NOTIFICATIONS_ENABLED', 'False'),
        'settings': {}
    }
    for k in keys:
        data['settings'][k] = {
            'env': os.getenv(k, 'True'),
            'runtime_override': _NOTIFY_RUNTIME_OVERRIDES.get(k),
            'effective': _notify_enabled(k, True),
        }
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
@mcp_tool_safe
def set_notification_settings(
    notify_trade_execution: Optional[bool] = None,
    notify_price_alerts: Optional[bool] = None,
    notify_daily_report: Optional[bool] = None,
    notify_system_errors: Optional[bool] = None,
    clear_overrides: bool = False,
) -> str:
    """设置通知开关（运行时覆盖，不修改 .env）。"""
    if clear_overrides:
        for k in list(_NOTIFY_RUNTIME_OVERRIDES.keys()):
            _NOTIFY_RUNTIME_OVERRIDES[k] = None

    if notify_trade_execution is not None:
        _NOTIFY_RUNTIME_OVERRIDES['NOTIFY_TRADE_EXECUTION'] = bool(notify_trade_execution)
    if notify_price_alerts is not None:
        _NOTIFY_RUNTIME_OVERRIDES['NOTIFY_PRICE_ALERTS'] = bool(notify_price_alerts)
    if notify_daily_report is not None:
        _NOTIFY_RUNTIME_OVERRIDES['NOTIFY_DAILY_REPORT'] = bool(notify_daily_report)
    if notify_system_errors is not None:
        _NOTIFY_RUNTIME_OVERRIDES['NOTIFY_SYSTEM_ERRORS'] = bool(notify_system_errors)

    return get_notification_settings()

# ============================================
# 3. 交易记录系统
# ============================================

def log_trade(order_id, symbol, side, amount, price, cost, status):
    """记录交易到 CSV"""
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ts = int(time.time())

    if USE_TRADE_DB and trade_store is not None:
        try:
            trade_store.insert_trade(
                order_id=str(order_id),
                symbol=str(symbol),
                side=str(side),
                amount=float(amount),
                price=float(price),
                cost=float(cost),
                status=str(status),
                time_str=time_str,
                timestamp=ts,
            )
        except Exception as e:
            logger.error(f"交易写入SQLite失败: {e}")

    file_exists = os.path.exists(TRADE_LOG_FILE)
    try:
        with _TRADE_CSV_LOCK:
            with open(TRADE_LOG_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['时间', '订单ID', '交易对', '方向', '数量', '价格', '总额', '状态'])
                writer.writerow([
                    time_str,
                    order_id, symbol, side.upper(), amount, price, cost, status
                ])
        logger.info(f"📝 交易记录: {side.upper()} {symbol} {amount}")
        send_trade_notification(order_id, symbol, side, amount, price, cost, status)
    except Exception as e:
        logger.error(f"记录失败: {e}")

def get_daily_traded_amount() -> float:
    """获取今日已交易总额"""
    if USE_TRADE_DB and trade_store is not None:
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            return float(trade_store.sum_cost_by_date_prefix(today))
        except Exception:
            pass
    if not os.path.exists(TRADE_LOG_FILE):
        return 0.0
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        total = 0.0
        with _TRADE_CSV_LOCK:
            with open(TRADE_LOG_FILE, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if row[0].startswith(today):
                        total += float(row[6])
        return total
    except:
        return 0.0

@mcp.tool()
@mcp_tool_safe
def get_trade_history(limit: int = 10) -> str:
    """
    查询交易历史记录。
    Args:
        limit: 显示最近多少条记录
    """
    try:
        recent = []

        if USE_TRADE_DB and trade_store is not None:
            try:
                rows = trade_store.list_trades(limit=int(limit) if limit else 10)
                for r in rows:
                    recent.append([
                        str(r.get('time_str') or ''),
                        str(r.get('order_id') or ''),
                        str(r.get('symbol') or ''),
                        str(r.get('side') or '').upper(),
                        str(r.get('amount') or ''),
                        str(r.get('price') or ''),
                        str(r.get('cost') or ''),
                        str(r.get('status') or ''),
                    ])
            except Exception:
                recent = []

        if not recent:
            if not os.path.exists(TRADE_LOG_FILE):
                return "📭 暂无交易记录"
            with _TRADE_CSV_LOCK:
                with open(TRADE_LOG_FILE, 'r', encoding='utf-8') as f:
                    trades = list(csv.reader(f))
            if len(trades) < 2:
                return "📭 交易记录为空"
            recent = trades[1:][-limit:][::-1]

        report = "📜 **交易历史**\n" + "─" * 30 + "\n"
        
        total_buy, total_sell = 0.0, 0.0
        for t in recent:
            emoji = "📈" if t[3] == "BUY" else "📉"
            report += f"{emoji} **{t[3]}** {t[2]}\n"
            report += f"   🕒 {t[0]}\n"
            report += f"   💰 数量: {t[4]} | 价格: {t[5]} | 总额: {t[6]} U\n\n"
            if t[3] == "BUY":
                total_buy += float(t[6])
            else:
                total_sell += float(t[6])
        
        report += "─" * 30 + "\n"
        report += f"📊 统计: 买入 {total_buy:.2f} U | 卖出 {total_sell:.2f} U"
        return report
    except Exception as e:
        return f"❌ 读取失败: {str(e)}"

@mcp.tool()
@mcp_tool_safe
def get_trade_statistics() -> str:
    """获取交易统计数据（今日/本周/本月）"""
    try:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        month_ago = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        
        stats = {'today': {'buy': 0, 'sell': 0, 'count': 0},
                 'week': {'buy': 0, 'sell': 0, 'count': 0},
                 'month': {'buy': 0, 'sell': 0, 'count': 0}}

        used_db = False
        if USE_TRADE_DB and trade_store is not None:
            try:
                stats['today'] = trade_store.stats_since_date_prefix(today)
                stats['week'] = trade_store.stats_since_date_prefix(week_ago)
                stats['month'] = trade_store.stats_since_date_prefix(month_ago)
                used_db = True
            except Exception:
                used_db = False

        if not used_db:
            if not os.path.exists(TRADE_LOG_FILE):
                return "📭 暂无交易数据"
            with _TRADE_CSV_LOCK:
                with open(TRADE_LOG_FILE, 'r', encoding='utf-8') as f:
                    for row in list(csv.reader(f))[1:]:
                        date = row[0][:10]
                        amt = float(row[6])
                        side = 'buy' if row[3] == 'BUY' else 'sell'
                        
                        if date >= today:
                            stats['today'][side] += amt
                            stats['today']['count'] += 1
                        if date >= week_ago:
                            stats['week'][side] += amt
                            stats['week']['count'] += 1
                        if date >= month_ago:
                            stats['month'][side] += amt
                            stats['month']['count'] += 1
        
        return (
            f"📊 **交易统计**\n"
            f"{'═' * 35}\n\n"
            f"**今日** ({stats['today']['count']} 笔)\n"
            f"  📈 买入: {stats['today']['buy']:.2f} U\n"
            f"  📉 卖出: {stats['today']['sell']:.2f} U\n\n"
            f"**本周** ({stats['week']['count']} 笔)\n"
            f"  📈 买入: {stats['week']['buy']:.2f} U\n"
            f"  📉 卖出: {stats['week']['sell']:.2f} U\n\n"
            f"**本月** ({stats['month']['count']} 笔)\n"
            f"  📈 买入: {stats['month']['buy']:.2f} U\n"
            f"  📉 卖出: {stats['month']['sell']:.2f} U"
        )
    except Exception as e:
        return f"❌ 统计失败: {str(e)}"

# ============================================
# 4. 技术分析系统
# ============================================

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """计算所有技术指标"""
    close = df['close'].astype(float)
    high = df['high'].astype(float)
    low = df['low'].astype(float)
    
    # RSI (14)
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(span=14, adjust=False).mean()
    avg_loss = loss.ewm(span=14, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # SMA
    df['SMA_7'] = close.rolling(window=7).mean()
    df['SMA_20'] = close.rolling(window=20).mean()
    df['SMA_50'] = close.rolling(window=50).mean()
    
    # EMA
    df['EMA_12'] = close.ewm(span=12, adjust=False).mean()
    df['EMA_26'] = close.ewm(span=26, adjust=False).mean()
    
    # MACD
    df['MACD_Line'] = df['EMA_12'] - df['EMA_26']
    df['Signal_Line'] = df['MACD_Line'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD_Line'] - df['Signal_Line']
    
    # Bollinger Bands
    std = close.rolling(window=20).std()
    df['BB_Upper'] = df['SMA_20'] + (std * 2)
    df['BB_Lower'] = df['SMA_20'] - (std * 2)
    df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['SMA_20'] * 100
    
    # ATR (Average True Range)
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()
    
    # Volume Analysis
    df['Volume_SMA'] = df['volume'].rolling(window=20).mean()
    df['Volume_Ratio'] = df['volume'] / df['Volume_SMA']
    
    return df.bfill().ffill()

@mcp.tool()
@mcp_tool_safe
def get_comprehensive_analysis(symbol: str = "BTC/USDT", timeframe: str = "1h") -> str:
    """
    获取综合技术分析报告。
    Args:
        symbol: 交易对 (如 BTC/USDT)
        timeframe: 时间周期 (1m, 5m, 15m, 1h, 4h, 1d)
    """
    try:
        exchange = get_exchange()
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=OHLCV_LIMIT_COMPREHENSIVE_ANALYSIS)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = calculate_indicators(df)
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        price = curr['close']
        
        # 趋势判断
        trend = "🟢 看涨" if price > curr['SMA_20'] > curr['SMA_50'] else \
                "🔴 看跌" if price < curr['SMA_20'] < curr['SMA_50'] else "🟡 震荡"
        
        # RSI 状态
        rsi = curr['RSI']
        rsi_state = "⚠️ 超买" if rsi > 70 else "💎 超卖" if rsi < 30 else "中性"
        
        # MACD 信号
        macd_signal = "📈 金叉" if curr['MACD_Line'] > curr['Signal_Line'] and prev['MACD_Line'] <= prev['Signal_Line'] else \
                      "📉 死叉" if curr['MACD_Line'] < curr['Signal_Line'] and prev['MACD_Line'] >= prev['Signal_Line'] else \
                      "多头" if curr['MACD_Hist'] > 0 else "空头"
        
        # 布林带位置
        bb_pos = (price - curr['BB_Lower']) / (curr['BB_Upper'] - curr['BB_Lower']) * 100
        bb_state = "上轨" if bb_pos > 80 else "下轨" if bb_pos < 20 else "中轨"
        
        # 成交量
        vol_state = "放量 📊" if curr['Volume_Ratio'] > 1.5 else "缩量" if curr['Volume_Ratio'] < 0.5 else "正常"
        
        # 24h 涨跌 (需要额外请求)
        ticker = exchange.fetch_ticker(symbol)
        change_24h = ticker.get('percentage', 0)
        
        return (
            f"📊 **{symbol} 技术分析** ({timeframe})\n"
            f"{'═' * 35}\n\n"
            f"💰 **价格**: ${price:,.2f} ({'+' if change_24h >= 0 else ''}{change_24h:.2f}% 24h)\n"
            f"📈 **趋势**: {trend}\n\n"
            f"**技术指标**\n"
            f"├─ RSI(14): {rsi:.1f} ({rsi_state})\n"
            f"├─ MACD: {macd_signal} ({curr['MACD_Hist']:.4f})\n"
            f"├─ 布林带: {bb_state} ({bb_pos:.0f}%)\n"
            f"├─ ATR(14): {curr['ATR']:.2f}\n"
            f"└─ 成交量: {vol_state} ({curr['Volume_Ratio']:.1f}x)\n\n"
            f"**均线**\n"
            f"├─ SMA7: ${curr['SMA_7']:.2f}\n"
            f"├─ SMA20: ${curr['SMA_20']:.2f}\n"
            f"└─ SMA50: ${curr['SMA_50']:.2f}"
        )
    except Exception as e:
        logger.error(f"分析失败: {e}")
        return f"❌ 分析错误: {str(e)}"

# --- Data Classes for Visualization ---
@dataclass
class CandleData:
    """K线数据（前端友好格式）"""
    timestamp: int       # Unix毫秒时间戳
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass
class IndicatorData:
    """指标数据"""
    name: str           # RSI, MACD, etc.
    values: List[Dict[str, Any]]  # [{timestamp: 123, value: 65.2}, ...]
    params: Dict[str, Any]        # {period: 14}

@dataclass
class VisualizationHint:
    """可视化建议（告诉Claude如何渲染）"""
    type: str           # "candlestick" | "line" | "gauge" | "table"
    priority: int       # 1=强烈推荐, 2=可选
    title: str
    description: str
    recommended_library: str  # "recharts" | "d3"

@dataclass
class MarketAnalysisOutput:
    """市场分析输出（Artifact友好）"""
    
    # 元信息
    symbol: str
    timeframe: str
    timestamp: str
    
    # 可视化数据
    candles: List[CandleData]
    indicators: List[IndicatorData]
    
    # 可视化建议
    visualizations: List[VisualizationHint]
    
    # 文字摘要（兜底）
    summary: str
    
    # 元标记（重要！）
    _artifact_metadata: Dict[str, Any]
    
    def to_dict(self):
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp,
            "data": {
                "candles": [asdict(c) for c in self.candles],
                "indicators": [asdict(i) for i in self.indicators]
            },
            "visualizations": [asdict(v) for v in self.visualizations],
            "summary": self.summary,
            "_artifact_metadata": {
                "version": "2.0",
                "supports_visualization": True,
                "recommended_artifact_type": "react",
                "data_format": "financial_chart"
            }
        }

@mcp.tool()
@mcp_tool_safe
def get_market_analysis(
    symbol: str = "BTC/USDT",
    timeframe: str = "1h",
    enable_visualization: bool = True
) -> str:
    """
    获取市场技术分析（支持可视化输出）。
    
    Args:
        symbol: 交易对 (如 BTC/USDT)
        timeframe: 时间周期 (1h, 4h, 1d)
        enable_visualization: 是否返回结构化数据以供前端/AI渲染图表
        
    Returns:
        如果 enable_visualization=True，返回包含可视化数据的JSON字符串
        如果 enable_visualization=False，返回传统Markdown文本
    """
    try:
        exchange = get_exchange()
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=OHLCV_LIMIT_MARKET_ANALYSIS)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = calculate_indicators(df)
        
        # 基础数据
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        price = curr['close']
        
        # --- 文本报告生成 (复用逻辑) ---
        trend = "🟢 看涨" if price > curr['SMA_20'] > curr['SMA_50'] else \
                "🔴 看跌" if price < curr['SMA_20'] < curr['SMA_50'] else "🟡 震荡"
        
        rsi = curr['RSI']
        rsi_state = "⚠️ 超买" if rsi > 70 else "💎 超卖" if rsi < 30 else "中性"
        
        macd_signal = "📈 金叉" if curr['MACD_Line'] > curr['Signal_Line'] and prev['MACD_Line'] <= prev['Signal_Line'] else \
                      "📉 死叉" if curr['MACD_Line'] < curr['Signal_Line'] and prev['MACD_Line'] >= prev['Signal_Line'] else \
                      "多头" if curr['MACD_Hist'] > 0 else "空头"
        
        bb_pos = (price - curr['BB_Lower']) / (curr['BB_Upper'] - curr['BB_Lower']) * 100
        bb_state = "上轨" if bb_pos > 80 else "下轨" if bb_pos < 20 else "中轨"
        
        vol_state = "放量 📊" if curr['Volume_Ratio'] > 1.5 else "缩量" if curr['Volume_Ratio'] < 0.5 else "正常"
        
        try:
            ticker = exchange.fetch_ticker(symbol)
            change_24h = ticker.get('percentage', 0)
        except:
            change_24h = 0
            
        summary_report = (
            f"📊 **{symbol} 技术分析** ({timeframe})\n"
            f"{'═' * 35}\n\n"
            f"💰 **价格**: ${price:,.2f} ({'+' if change_24h >= 0 else ''}{change_24h:.2f}% 24h)\n"
            f"📈 **趋势**: {trend}\n\n"
            f"**技术指标**\n"
            f"├─ RSI(14): {rsi:.1f} ({rsi_state})\n"
            f"├─ MACD: {macd_signal} ({curr['MACD_Hist']:.4f})\n"
            f"├─ 布林带: {bb_state} ({bb_pos:.0f}%)\n"
            f"├─ ATR(14): {curr['ATR']:.2f}\n"
            f"└─ 成交量: {vol_state} ({curr['Volume_Ratio']:.1f}x)\n"
        )

        if not enable_visualization:
            return summary_report
            
        # --- Visualization Data Generation ---
        
        # 1. Candles
        candles_data = [
            CandleData(
                timestamp=int(row['timestamp']),
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=float(row['volume'])
            )
            for _, row in df.iterrows()
        ]
        
        # 2. Indicators
        indicators_data = []
        
        # RSI
        rsi_vals = [{"timestamp": int(ts), "value": float(val)} 
                   for ts, val in zip(df['timestamp'], df['RSI']) if not pd.isna(val)]
        indicators_data.append(IndicatorData(name="RSI", values=rsi_vals, params={"period": 14}))
        
        # MACD (Line, Signal, Hist)
        # 简化处理，只传 MACD Line 和 Signal Line 供绘图，Hist 可以前端算或再加
        macd_vals = [{"timestamp": int(ts), "value": float(val)} 
                    for ts, val in zip(df['timestamp'], df['MACD_Line']) if not pd.isna(val)]
        signal_vals = [{"timestamp": int(ts), "value": float(val)} 
                      for ts, val in zip(df['timestamp'], df['Signal_Line']) if not pd.isna(val)]
        indicators_data.append(IndicatorData(name="MACD", values=macd_vals, params={"type": "line"}))
        indicators_data.append(IndicatorData(name="MACD_Signal", values=signal_vals, params={"type": "signal"}))
        
        # SMA
        sma20_vals = [{"timestamp": int(ts), "value": float(val)} 
                     for ts, val in zip(df['timestamp'], df['SMA_20']) if not pd.isna(val)]
        indicators_data.append(IndicatorData(name="SMA20", values=sma20_vals, params={"period": 20}))
        
        # 3. Output
        output = MarketAnalysisOutput(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=datetime.now().isoformat(),
            candles=candles_data,
            indicators=indicators_data,
            visualizations=[
                VisualizationHint(
                    type="candlestick",
                    priority=1,
                    title=f"{symbol} 价格走势",
                    description="显示开盘、收盘、最高、最低价及SMA20",
                    recommended_library="recharts"
                ),
                VisualizationHint(
                    type="line",
                    priority=2,
                    title="RSI 动量指标",
                    description="相对强弱指标 (14)",
                    recommended_library="recharts"
                )
            ],
            summary=summary_report,
            _artifact_metadata={
                "version": "2.0",
                "supports_visualization": True
            }
        )
        
        return json.dumps(output.to_dict(), ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Visualization Analysis Failed: {e}")
        # Fallback to simple error message but JSON formatted if possible? 
        # Or just string error as per wrapper
        raise e

@mcp.tool()
@mcp_tool_safe
def get_market_sentiment(symbol: str = "BTC/USDT") -> str:
    """
    获取市场情绪评分和交易建议。
    评分 0-100: 0-20 极度恐慌, 80-100 极度贪婪
    """
    try:
        exchange = get_exchange()
        ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=OHLCV_LIMIT_SENTIMENT)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = calculate_indicators(df)
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        score = 50
        factors = []
        
        # RSI (权重 25%)
        if curr['RSI'] < 30:
            score += 20
            factors.append("RSI 超卖 (+20)")
        elif curr['RSI'] > 70:
            score -= 20
            factors.append("RSI 超买 (-20)")
        elif curr['RSI'] > 50:
            score += 5
            factors.append("RSI 偏多 (+5)")
        else:
            score -= 5
            factors.append("RSI 偏空 (-5)")
        
        # 趋势 (权重 25%)
        if curr['close'] > curr['SMA_20'] > curr['SMA_50']:
            score += 15
            factors.append("强势上涨趋势 (+15)")
        elif curr['close'] < curr['SMA_20'] < curr['SMA_50']:
            score -= 15
            factors.append("强势下跌趋势 (-15)")
        elif curr['close'] > curr['SMA_20']:
            score += 8
            factors.append("短期看涨 (+8)")
        else:
            score -= 8
            factors.append("短期看跌 (-8)")
        
        # MACD (权重 20%)
        if curr['MACD_Hist'] > 0 and curr['MACD_Hist'] > prev['MACD_Hist']:
            score += 10
            factors.append("MACD 增强 (+10)")
        elif curr['MACD_Hist'] < 0 and curr['MACD_Hist'] < prev['MACD_Hist']:
            score -= 10
            factors.append("MACD 减弱 (-10)")
        
        # 成交量 (权重 15%)
        if curr['Volume_Ratio'] > 1.5:
            if curr['close'] > prev['close']:
                score += 8
                factors.append("放量上涨 (+8)")
            else:
                score -= 8
                factors.append("放量下跌 (-8)")
        
        score = max(0, min(100, score))
        
        # 情绪标签
        if score >= 80:
            sentiment = "🤑 极度贪婪"
            suggestion = "⚠️ 市场过热，注意风险"
        elif score >= 60:
            sentiment = "😃 贪婪"
            suggestion = "📈 多头趋势，可考虑持有"
        elif score >= 40:
            sentiment = "😐 中性"
            suggestion = "⏸️ 观望为主，等待信号"
        elif score >= 20:
            sentiment = "😨 恐慌"
            suggestion = "💎 可能是买入机会"
        else:
            sentiment = "😱 极度恐慌"
            suggestion = "🎯 逆向投资时机"
        
        factors_str = "\n".join([f"  • {f}" for f in factors])
        
        return (
            f"🌡️ **{symbol} 市场情绪**\n"
            f"{'═' * 30}\n\n"
            f"**评分**: {score}/100\n"
            f"**状态**: {sentiment}\n\n"
            f"**分析因素**:\n{factors_str}\n\n"
            f"**建议**: {suggestion}"
        )
    except Exception as e:
        return f"❌ 分析失败: {str(e)}"

@mcp.tool()
@mcp_tool_safe
def get_multi_symbol_overview() -> str:
    """获取多个主流币种的快速概览"""
    try:
        exchange = get_exchange()
        symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT']
        
        report = "📊 **主流币种快速概览**\n" + "═" * 35 + "\n\n"
        
        for symbol in symbols:
            try:
                ticker = exchange.fetch_ticker(symbol)
                ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=OHLCV_LIMIT_OVERVIEW)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df = calculate_indicators(df)
                rsi = df.iloc[-1]['RSI']
                
                change = ticker.get('percentage', 0)
                emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
                rsi_emoji = "⚠️" if rsi > 70 else "💎" if rsi < 30 else ""
                
                report += f"{emoji} **{symbol.replace('/USDT', '')}**\n"
                report += f"   ${ticker['last']:,.2f} ({'+' if change >= 0 else ''}{change:.2f}%)\n"
                report += f"   RSI: {rsi:.0f} {rsi_emoji}\n\n"
            except:
                continue
        
        return report
    except Exception as e:
        return f"❌ 获取失败: {str(e)}"

# ============================================
# 5. AI 智能分析决策系统 🤖
# ============================================

@mcp.tool()
@mcp_tool_safe
def get_ai_trading_advice(symbol: str = "BTC/USDT", mode: str = "simple") -> str:
    """
    AI 智能交易建议 - 双模式分析系统。
    Args:
        symbol: 交易对 (如 BTC/USDT)
        mode: "simple" (新手模式) 或 "professional" (专业模式)
    """
    try:
        exchange = get_exchange()
        ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=OHLCV_LIMIT_SIGNALS)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = calculate_indicators(df)
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        price = curr['close']
        
        # 计算信号
        signals = {
            'buy': 0,
            'sell': 0,
            'neutral': 0
        }
        
        # RSI 信号
        if curr['RSI'] < 30:
            signals['buy'] += 1
        elif curr['RSI'] > 70:
            signals['sell'] += 1
        else:
            signals['neutral'] += 1
        
        # 趋势信号
        if price > curr['SMA_20'] > curr['SMA_50']:
            signals['buy'] += 1
        elif price < curr['SMA_20'] < curr['SMA_50']:
            signals['sell'] += 1
        else:
            signals['neutral'] += 1
        
        # MACD 信号
        if curr['MACD_Hist'] > 0 and curr['MACD_Hist'] > prev['MACD_Hist']:
            signals['buy'] += 1
        elif curr['MACD_Hist'] < 0 and curr['MACD_Hist'] < prev['MACD_Hist']:
            signals['sell'] += 1
        else:
            signals['neutral'] += 1
        
        # 布林带信号
        if price < curr['BB_Lower']:
            signals['buy'] += 1
        elif price > curr['BB_Upper']:
            signals['sell'] += 1
        else:
            signals['neutral'] += 1
        
        # 成交量信号
        if curr['Volume_Ratio'] > 1.5 and price > prev['close']:
            signals['buy'] += 1
        elif curr['Volume_Ratio'] > 1.5 and price < prev['close']:
            signals['sell'] += 1
        else:
            signals['neutral'] += 1
        
        # 确定主要方向
        total = sum(signals.values())
        buy_pct = signals['buy'] / total * 100
        sell_pct = signals['sell'] / total * 100
        
        if buy_pct > sell_pct and buy_pct > 40:
            direction = "buy"
            confidence = buy_pct
            trend_desc = "上涨"
        elif sell_pct > buy_pct and sell_pct > 40:
            direction = "sell"
            confidence = sell_pct
            trend_desc = "下跌"
        else:
            direction = "hold"
            confidence = signals['neutral'] / total * 100
            trend_desc = "震荡"
        
        # 计算支撑阻力位 (简单版: 基于近期高低点)
        recent_highs = df['high'].tail(20).nlargest(3).mean()
        recent_lows = df['low'].tail(20).nsmallest(3).mean()
        support = recent_lows
        resistance = recent_highs
        
        # 止损止盈计算
        atr = curr['ATR']
        stop_loss = price - (atr * 2) if direction == "buy" else price + (atr * 2)
        take_profit_1 = price + (atr * 3) if direction == "buy" else price - (atr * 3)
        take_profit_2 = price + (atr * 5) if direction == "buy" else price - (atr * 5)
        
        # 信心星级
        stars = "★" * int(confidence / 20) + "☆" * (5 - int(confidence / 20))
        
        ticker = exchange.fetch_ticker(symbol)
        change_24h = ticker.get('percentage', 0)
        
        if mode.lower() == "simple":
            # 🌱 新手模式: 简单直接
            action_emoji = "📈" if direction == "buy" else "📉" if direction == "sell" else "⏸️"
            action_text = "适合买入" if direction == "buy" else "建议卖出" if direction == "sell" else "观望为主"
            
            situation = f"价格正在{trend_desc}"
            
            risk_tip = f"设置止损在 ${stop_loss:,.2f} {'以下' if direction == 'buy' else '以上'}，保护本金安全。"
            
            tips = []
            if curr['RSI'] < 30:
                tips.append("RSI 指标显示当前是超卖状态，通常是买入好时机。")
            elif curr['RSI'] > 70:
                tips.append("RSI 指标显示当前是超买状态，价格可能回调。")
            else:
                tips.append("RSI 指标显示当前不是极端状态，还有上涨/下跌空间。")
            
            if curr['Volume_Ratio'] > 1.5:
                tips.append("成交量放大，说明市场交易活跃，趋势可能延续。")
            
            return (
                f"🤖 **AI 交易建议 - {symbol}**\n\n"
                f"📊 **当前状况**: {situation}\n"
                f"{action_emoji} **建议操作**: {action_text}\n"
                f"⭐ **信心指数**: {stars} ({confidence:.0f}%)\n\n"
                f"💡 **简单解释**:\n"
                f"{symbol.split('/')[0]} 目前价格 ${price:,.2f}，24h {'+' if change_24h >= 0 else ''}{change_24h:.1f}%。\n"
                f"根据多个技术指标分析，市场呈现{trend_desc}趋势。\n"
                f"{'建议小额试探性买入。' if direction == 'buy' else '建议减仓或观望。' if direction == 'sell' else '建议等待更明确信号。'}\n\n"
                f"⚠️ **风险提示**: \n{risk_tip}\n\n"
                f"🎓 **小贴士**:\n" + "\n".join([f"• {tip}" for tip in tips])
            )
        
        else:
            # 📊 专业模式: 详细分析
            # ADX 趋势强度 (简化计算)
            adx_value = min(100, curr['ATR'] / price * 1000)
            adx_status = "强趋势" if adx_value > 25 else "弱趋势"
            
            # 连续K线统计
            consecutive_up = 0
            for i in range(len(df) - 1, 0, -1):
                if df.iloc[i]['close'] > df.iloc[i]['open']:
                    consecutive_up += 1
                else:
                    break
            consecutive_down = 0
            for i in range(len(df) - 1, 0, -1):
                if df.iloc[i]['close'] < df.iloc[i]['open']:
                    consecutive_down += 1
                else:
                    break
            
            trend_persist = "高" if max(consecutive_up, consecutive_down) >= 3 else "中" if max(consecutive_up, consecutive_down) == 2 else "低"
            
            # 技术指标状态
            indicators_table = []
            indicators_table.append(("RSI(14)", f"{curr['RSI']:.1f}", "超买" if curr['RSI'] > 70 else "超卖" if curr['RSI'] < 30 else "中性"))
            indicators_table.append(("MACD", f"{curr['MACD_Hist']:.2f}", "多头" if curr['MACD_Hist'] > 0 else "空头"))
            indicators_table.append(("布林带位置", f"{(price-curr['BB_Lower'])/(curr['BB_Upper']-curr['BB_Lower'])*100:.0f}%", "上轨" if price > curr['BB_Upper'] else "下轨" if price < curr['BB_Lower'] else "中轨"))
            indicators_table.append(("ATR%", f"{curr['ATR']/price*100:.2f}%", "高波动" if curr['ATR']/price > 0.03 else "低波动"))
            indicators_table.append(("成交量", f"{curr['Volume_Ratio']:.1f}x", "放量" if curr['Volume_Ratio'] > 1.5 else "缩量"))
            
            # 决策依据
            reasons = []
            if price > curr['SMA_20'] > curr['SMA_50']:
                reasons.append("价格站稳20/50日均线，趋势确立")
            if curr['MACD_Hist'] > 0 and curr['MACD_Hist'] > prev['MACD_Hist']:
                reasons.append("MACD 柱状图持续放大，动能增强")
            if curr['Volume_Ratio'] > 1.2:
                reasons.append("成交量配合良好")
            if curr['RSI'] < 70 and curr['RSI'] > 30:
                reasons.append("RSI 处于健康区间")
            
            # 风险因素
            risks = []
            if curr['RSI'] > 65:
                risks.append("RSI 接近超买区，注意短期回调")
            if curr['Volume_Ratio'] < 0.7:
                risks.append("成交量萎缩，趋势可能减弱")
            if abs(price - resistance) / price < 0.02:
                risks.append(f"${resistance:,.0f} 存在较强阻力")
            
            return (
                f"🤖 **AI 专业分析报告 - {symbol}**\n"
                f"{'═' * 40}\n\n"
                f"📈 **趋势分析**\n"
                f"├─ 主趋势: {'多头' if price > curr['SMA_20'] > curr['SMA_50'] else '空头' if price < curr['SMA_20'] < curr['SMA_50'] else '震荡'} "
                f"({'价格 > SMA20 > SMA50' if price > curr['SMA_50'] else '价格 < SMA20 < SMA50' if price < curr['SMA_50'] else '区间震荡'})\n"
                f"├─ 短期趋势: {trend_desc} (EMA12 {'>' if curr['EMA_12'] > curr['EMA_26'] else '<'} EMA26)\n"
                f"├─ 趋势强度: {adx_value:.1f} ({adx_status})\n"
                f"└─ 趋势持续性: {trend_persist} ({'连续' + str(max(consecutive_up, consecutive_down)) + '根' + ('阳线' if consecutive_up > consecutive_down else '阴线') if max(consecutive_up, consecutive_down) > 0 else '震荡'})\n\n"
                f"📊 **技术指标**\n"
                + "\n".join([f"├─ {ind[0]}: {ind[1]} ({ind[2]})" for ind in indicators_table[:-1]]) +
                f"\n└─ {indicators_table[-1][0]}: {indicators_table[-1][1]} ({indicators_table[-1][2]})\n\n"
                f"🎯 **关键价位**\n"
                f"├─ 阻力位: ${resistance:,.2f}\n"
                f"├─ 支撑位: ${support:,.2f}\n"
                f"├─ 当前价: ${price:,.2f}\n"
                f"└─ 24h 涨跌: {'+' if change_24h >= 0 else ''}{change_24h:.2f}%\n\n"
                f"📉 **风险评估**\n"
                f"├─ 波动率 (ATR%): {curr['ATR']/price*100:.2f}% ({'高' if curr['ATR']/price > 0.03 else '中' if curr['ATR']/price > 0.015 else '低'})\n"
                f"├─ 流动性: {'高' if ticker.get('quoteVolume', 0) > 1e9 else '中' if ticker.get('quoteVolume', 0) > 1e8 else '低'}\n"
                f"└─ 建议杠杆: 最高 {3 if curr['ATR']/price < 0.02 else 2 if curr['ATR']/price < 0.03 else 1}x\n\n"
                f"🤖 **AI 综合决策**\n"
                f"┌{'─' * 38}┐\n"
                f"│ 方向: {'📈 做多' if direction == 'buy' else '📉 做空' if direction == 'sell' else '⏸️ 观望'}                            │\n"
                f"│ 信心: {confidence:.0f}% ({'高' if confidence > 70 else '中高' if confidence > 50 else '中' if confidence > 30 else '低'})                         │\n"
                f"│ 时效: 短期 (1-3天)                     │\n"
                f"│                                        │\n"
                f"│ {'建议入场: $' + f'{price*0.995:,.2f}' + ' - $' + f'{price*1.005:,.2f}' if direction != 'hold' else '建议: 等待更明确信号'}       │\n"
                f"│ {'止损价位: $' + f'{stop_loss:,.2f}' + f' ({(stop_loss-price)/price*100:+.1f}%)' if direction != 'hold' else ''}      │\n"
                f"│ {'止盈目标:' if direction != 'hold' else ''}                              │\n"
                f"│ {'  T1: $' + f'{take_profit_1:,.2f}' + f' ({(take_profit_1-price)/price*100:+.1f}%)' + ' - 减仓 50%' if direction != 'hold' else ''}   │\n"
                f"│ {'  T2: $' + f'{take_profit_2:,.2f}' + f' ({(take_profit_2-price)/price*100:+.1f}%)' + ' - 清仓' if direction != 'hold' else ''}       │\n"
                f"│                                        │\n"
                f"│ 风险回报比: {abs((take_profit_1-price)/(price-stop_loss)):.1f}:1" + (" " * 19 if direction != 'hold' else " " * 24) + "│\n"
                f"└{'─' * 38}┘\n\n"
                f"📝 **决策依据**\n"
                + ("" if not reasons else "\n".join([f"{i+1}. {r}" for i, r in enumerate(reasons)])) +
                f"\n\n⚠️ **风险因素**\n"
                + ("• 当前信号不够明确，建议等待" if not risks else "\n".join([f"• {r}" for r in risks]))
            )
    
    except Exception as e:
        logger.error(f"AI 分析失败: {e}")
        return f"❌ 分析错误: {str(e)}"

@mcp.tool()
@mcp_tool_safe
def get_market_overview(mode: str = "simple") -> str:
    """
    获取加密货币市场全景分析。
    Args:
        mode: "simple" (新手概览) 或 "professional" (专业全景)
    """
    try:
        exchange = get_exchange()
        symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT', 'ADA/USDT']
        
        market_data = []
        for symbol in symbols:
            try:
                ticker = exchange.fetch_ticker(symbol)
                ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=OHLCV_LIMIT_MARKET_OVERVIEW)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df = calculate_indicators(df)
                curr = df.iloc[-1]
                
                # 计算简单信号
                buy_signals = 0
                sell_signals = 0
                
                if curr['RSI'] < 35:
                    buy_signals += 1
                elif curr['RSI'] > 65:
                    sell_signals += 1
                
                if curr['close'] > curr['SMA_20']:
                    buy_signals += 1
                else:
                    sell_signals += 1
                
                if curr['MACD_Hist'] > 0:
                    buy_signals += 1
                else:
                    sell_signals += 1
                
                signal = "buy" if buy_signals > sell_signals else "sell" if sell_signals > buy_signals else "neutral"
                
                market_data.append({
                    'symbol': symbol,
                    'price': ticker['last'],
                    'change': ticker.get('percentage', 0),
                    'rsi': curr['RSI'],
                    'signal': signal,
                    'trend_score': (buy_signals / 3) * 100 if signal == 'buy' else ((3 - sell_signals) / 3) * 100,
                    'momentum_score': min(100, abs(curr['MACD_Hist']) * 100),
                    'volatility_score': min(100, (curr['ATR'] / curr['close']) * 1000),
                    'volume_ratio': curr['Volume_Ratio']
                })
            except:
                continue
        
        if mode.lower() == "simple":
            # 🌱 简单模式: 红绿灯系统
            report = "🚦 **市场快速扫描**\n\n"
            
            recommendations = []
            for data in market_data:
                emoji = "🟢" if data['signal'] == 'buy' else "🔴" if data['signal'] == 'sell' else "🟡"
                coin = data['symbol'].split('/')[0]
                advice = "可以关注" if data['signal'] == 'buy' else "暂时回避" if data['signal'] == 'sell' else "观望为主"
                
                report += f"{emoji} **{coin}**  ${data['price']:,.2f}  {'+' if data['change'] >= 0 else ''}{data['change']:.1f}%  → {advice}\n"
                
                if data['signal'] == 'buy':
                    recommendations.append(coin)
            
            if recommendations:
                report += f"\n💡 **今日建议**: 关注 {' 和 '.join(recommendations[:2])}，趋势较好"
            else:
                report += f"\n💡 **今日建议**: 市场整体偏弱，建议观望"
            
            return report
        
        else:
            # 📊 专业模式: 多维度打分
            report = "📊 **主流币种评分矩阵** (满分100)\n"
            report += "┌" + "─" * 9 + "┬" + "─" * 7 + "┬" + "─" * 7 + "┬" + "─" * 7 + "┬" + "─" * 7 + "┬" + "─" * 7 + "┐\n"
            report += "│ 币种    │ 趋势  │ 动量  │ 波动  │ 成交  │ 综合  │\n"
            report += "├" + "─" * 9 + "┼" + "─" * 7 + "┼" + "─" * 7 + "┼" + "─" * 7 + "┼" + "─" * 7 + "┼" + "─" * 7 + "┤\n"
            
            for data in market_data:
                coin = data['symbol'].split('/')[0]
                trend = int(data['trend_score'])
                momentum = int(data['momentum_score'])
                volatility = 100 - int(data['volatility_score'])  # 低波动得高分
                volume = int(min(100, data['volume_ratio'] * 50))
                overall = int((trend + momentum + volatility + volume) / 4)
                
                report += f"│ {coin:<7} │ {trend:<5} │ {momentum:<5} │ {volatility:<5} │ {volume:<5} │ {overall:<5} │\n"
            
            report += "└" + "─" * 9 + "┴" + "─" * 7 + "┴" + "─" * 7 + "┴" + "─" * 7 + "┴" + "─" * 7 + "┴" + "─" * 7 + "┘\n\n"
            
            # 推荐
            sorted_data = sorted(market_data, key=lambda x: (x['trend_score'] + x['momentum_score']) / 2, reverse=True)
            report += "🏆 **推荐关注**: " + ", ".join([d['symbol'].split('/')[0] for d in sorted_data[:2]])
            report += "\n⚠️ **谨慎对待**: " + ", ".join([d['symbol'].split('/')[0] for d in sorted_data[-2:]])
            
            return report
    
    except Exception as e:
        logger.error(f"市场概览失败: {e}")
        return f"❌ 获取失败: {str(e)}"

@mcp.tool()
@mcp_tool_safe
def get_trading_signals(symbol: str = "BTC/USDT") -> str:
    """
    获取多指标交易信号汇总。
    返回: 买入/卖出/持有 信号统计和综合评分
    """
    try:
        exchange = get_exchange()
        ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=OHLCV_LIMIT_SIGNALS)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = calculate_indicators(df)
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        signals = []
        buy_count = 0
        sell_count = 0
        neutral_count = 0
        
        # RSI 信号
        if curr['RSI'] < 30:
            signals.append(("RSI", "买入", "超卖区域"))
            buy_count += 1
        elif curr['RSI'] > 70:
            signals.append(("RSI", "卖出", "超买区域"))
            sell_count += 1
        else:
            signals.append(("RSI", "中性", f"数值 {curr['RSI']:.0f}"))
            neutral_count += 1
        
        # SMA 交叉
        if curr['SMA_7'] > curr['SMA_20'] and prev['SMA_7'] <= prev['SMA_20']:
            signals.append(("SMA 交叉", "买入", "短期均线上穿"))
            buy_count += 1
        elif curr['SMA_7'] < curr['SMA_20'] and prev['SMA_7'] >= prev['SMA_20']:
            signals.append(("SMA 交叉", "卖出", "短期均线下穿"))
            sell_count += 1
        else:
            signals.append(("SMA 交叉", "中性", "无交叉"))
            neutral_count += 1
        
        # MACD
        if curr['MACD_Line'] > curr['Signal_Line']:
            signals.append(("MACD", "买入", "MACD 在信号线上方"))
            buy_count += 1
        else:
            signals.append(("MACD", "卖出", "MACD 在信号线下方"))
            sell_count += 1
        
        # 布林带
        if curr['close'] < curr['BB_Lower']:
            signals.append(("布林带", "买入", "跌破下轨"))
            buy_count += 1
        elif curr['close'] > curr['BB_Upper']:
            signals.append(("布林带", "卖出", "突破上轨"))
            sell_count += 1
        else:
            signals.append(("布林带", "中性", "在轨道内"))
            neutral_count += 1
        
        # 成交量
        if curr['Volume_Ratio'] > 1.5 and curr['close'] > prev['close']:
            signals.append(("成交量", "买入", "放量上涨"))
            buy_count += 1
        elif curr['Volume_Ratio'] > 1.5 and curr['close'] < prev['close']:
            signals.append(("成交量", "卖出", "放量下跌"))
            sell_count += 1
        else:
            signals.append(("成交量", "中性", "量能正常"))
            neutral_count += 1
        
        # 趋势
        if curr['close'] > curr['SMA_20'] > curr['SMA_50']:
            signals.append(("趋势", "买入", "多头排列"))
            buy_count += 1
        elif curr['close'] < curr['SMA_20'] < curr['SMA_50']:
            signals.append(("趋势", "卖出", "空头排列"))
            sell_count += 1
        else:
            signals.append(("趋势", "中性", "震荡"))
            neutral_count += 1
        
        total = buy_count + sell_count + neutral_count
        
        # 综合建议
        if buy_count > sell_count and buy_count > neutral_count:
            recommendation = f"📈 买入 ({buy_count}/{total})"
        elif sell_count > buy_count and sell_count > neutral_count:
            recommendation = f"📉 卖出 ({sell_count}/{total})"
        else:
            recommendation = f"⏸️ 持有 ({neutral_count}/{total})"
        
        # 生成进度条
        buy_bar = "█" * buy_count + "░" * (total - buy_count)
        sell_bar = "█" * sell_count + "░" * (total - sell_count)
        neutral_bar = "█" * neutral_count + "░" * (total - neutral_count)
        
        report = (
            f"📊 **{symbol} 信号汇总**\n\n"
            f"买入信号: {buy_bar} {buy_count}/{total}\n"
            f"卖出信号: {sell_bar} {sell_count}/{total}\n"
            f"中性信号: {neutral_bar} {neutral_count}/{total}\n\n"
            f"**综合建议**: {recommendation}\n\n"
            f"**信号明细**:\n"
        )
        
        for sig in signals:
            emoji = "✅" if sig[1] == "买入" else "❌" if sig[1] == "卖出" else "⚪"
            report += f"{emoji} {sig[0]} → {sig[1]} ({sig[2]})\n"
        
        return report
    
    except Exception as e:
        logger.error(f"信号汇总失败: {e}")
        return f"❌ 获取失败: {str(e)}"

@mcp.tool()
@mcp_tool_safe
def get_position_recommendation(
    symbol: str = "BTC/USDT",
    account_balance: float = None,
    risk_tolerance: str = "moderate"
) -> str:
    """
    基于风险偏好的智能仓位建议。
    
    Args:
        symbol: 交易对 (如 BTC/USDT)
        account_balance: 账户余额 (USDT)，不指定则自动获取
        risk_tolerance: 风险偏好
            - "conservative" 保守型 (1% 风险)
            - "moderate" 稳健型 (2% 风险) 【默认】
            - "aggressive" 激进型 (5% 风险)
    """
    try:
        exchange = get_exchange()
        
        # 获取账户余额
        if account_balance is None:
            balance = exchange.fetch_balance()
            account_balance = balance['free'].get('USDT', 0)
            if account_balance == 0:
                return "❌ 账户 USDT 余额为 0，无法计算仓位"
        
        # 获取当前价格和技术指标
        ticker = exchange.fetch_ticker(symbol)
        ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=OHLCV_LIMIT_SIGNALS)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = calculate_indicators(df)
        
        curr = df.iloc[-1]
        price = ticker['last']
        atr = curr['ATR']
        
        # 风险参数
        risk_params = {
            'conservative': {'risk_pct': 1.0, 'leverage': 1, 'stop_atr': 2.5, 'name': '保守型'},
            'moderate': {'risk_pct': 2.0, 'leverage': 2, 'stop_atr': 2.0, 'name': '稳健型'},
            'aggressive': {'risk_pct': 5.0, 'leverage': 3, 'stop_atr': 1.5, 'name': '激进型'}
        }
        
        params = risk_params.get(risk_tolerance, risk_params['moderate'])
        risk_amount = account_balance * (params['risk_pct'] / 100)
        
        # 计算止损位 (基于 ATR)
        stop_loss = price - (atr * params['stop_atr'])
        stop_distance = price - stop_loss
        
        # 计算仓位大小
        position_size = risk_amount / stop_distance
        position_value = position_size * price
        
        # 入场价格区间 (当前价 ± 0.5%)
        entry_low = price * 0.995
        entry_high = price * 1.005
        
        # 止盈位 (1:2 和 1:3 风险回报)
        take_profit_1 = price + (stop_distance * 2)
        take_profit_2 = price + (stop_distance * 3)
        
        # 计算盈亏
        max_loss = -risk_amount
        profit_1 = (take_profit_1 - price) * position_size
        profit_2 = (take_profit_2 - price) * position_size
        
        # 仓位占比
        position_pct = (position_value / account_balance) * 100
        
        # 建议杠杆后的调整
        margin_required = position_value
        if params['leverage'] > 1:
            position_size_leveraged = position_size * params['leverage']
            position_value_leveraged = position_size_leveraged * price
            margin_required = position_value_leveraged / params['leverage']
            leverage_note = f"\n💰 **需要保证金**: ${margin_required:,.2f} USDT"
        else:
            leverage_note = ""
        
        logger.info(f"仓位建议: {symbol} {params['name']} 风险={params['risk_pct']}% 仓位={position_size:.6f}")
        
        return (
            f"💼 **{symbol} 智能仓位建议**\n"
            f"{'═' * 40}\n\n"
            f"📊 **账户信息**\n"
            f"├─ 可用余额: ${account_balance:,.2f} USDT\n"
            f"├─ 风险偏好: {params['name']} ({params['risk_pct']}% 风险)\n"
            f"└─ 最大损失: ${risk_amount:,.2f} USDT\n\n"
            f"📈 **市场数据**\n"
            f"├─ 当前价: ${price:,.2f}\n"
            f"├─ ATR(14): ${atr:,.2f}\n"
            f"├─ 波动率: {atr/price*100:.2f}%\n"
            f"└─ 24h 涨跌: {ticker.get('percentage', 0):+.2f}%\n\n"
            f"🎯 **仓位建议**\n"
            f"├─ 建议数量: {position_size:.6f} {symbol.split('/')[0]}\n"
            f"├─ 仓位价值: ${position_value:,.2f}\n"
            f"├─ 占总资金: {position_pct:.1f}%\n"
            f"└─ 建议杠杆: {params['leverage']}x\n"
            f"{leverage_note}\n\n"
            f"📍 **交易计划**\n"
            f"├─ 入场区间: ${entry_low:,.2f} - ${entry_high:,.2f}\n"
            f"├─ 止损价位: ${stop_loss:,.2f} ({(stop_loss-price)/price*100:+.2f}%)\n"
            f"├─ 止盈目标 1: ${take_profit_1:,.2f} ({(take_profit_1-price)/price*100:+.2f}%)\n"
            f"└─ 止盈目标 2: ${take_profit_2:,.2f} ({(take_profit_2-price)/price*100:+.2f}%)\n\n"
            f"💵 **盈亏预测**\n"
            f"├─ 最大损失: {max_loss:,.2f} USDT ({max_loss/account_balance*100:+.2f}%)\n"
            f"├─ T1 盈利: +{profit_1:,.2f} USDT ({profit_1/account_balance*100:+.2f}%)\n"
            f"└─ T2 盈利: +{profit_2:,.2f} USDT ({profit_2/account_balance*100:+.2f}%)\n\n"
            f"📊 **风险回报比**\n"
            f"├─ T1: 1:{abs(profit_1/risk_amount):.1f}\n"
            f"└─ T2: 1:{abs(profit_2/risk_amount):.1f}\n\n"
            f"⚠️ **风险提示**\n"
            f"• 严格执行止损，避免仓位过重\n"
            f"• 分批入场和出场，降低风险\n"
            f"• {'高杠杆高风险，谨慎使用' if params['leverage'] > 1 else '现货交易相对安全'}\n"
            f"• 根据市场变化及时调整策略"
        )
    
    except Exception as e:
        logger.error(f"仓位建议失败: {e}")
        return f"❌ 计算失败: {str(e)}"

# ============================================
# 6. 账户管理系统
# ============================================

@mcp.tool()
@mcp_tool_safe
def get_account_summary() -> str:
    """获取账户资产详情（优化版：批量获取价格）"""
    try:
        exchange = get_exchange()
        logger.debug("⏱️ 开始获取账户信息...")
        start_time = time.time()
        
        # 获取余额
        balance = exchange.fetch_balance()
        logger.debug(f"⏱️ 获取余额耗时: {time.time() - start_time:.2f}s")
        
        usdt_balance = balance['total'].get('USDT', 0)
        free_usdt = balance['free'].get('USDT', 0)
        total_value = usdt_balance
        positions = []
        
        # 找出需要查询的币种
        coins_to_fetch = []
        for coin, amount in balance['total'].items():
            if amount > 0 and coin not in {'USDT', 'BUSD', 'USDC'}:
                coins_to_fetch.append(coin)
        
        # 批量获取所有 ticker（大幅提速）
        tickers = {}
        if coins_to_fetch:
            ticker_start = time.time()
            try:
                all_tickers = exchange.fetch_tickers()  # 一次获取所有价格
                logger.debug(f"⏱️ 批量获取 ticker 耗时: {time.time() - ticker_start:.2f}s")
                tickers = all_tickers
            except:
                # 如果批量失败，降级到逐个获取
                logger.warning("⚠️ 批量获取失败，使用逐个获取")
                for coin in coins_to_fetch:
                    try:
                        ticker = exchange.fetch_ticker(f"{coin}/USDT")
                        tickers[f"{coin}/USDT"] = ticker
                    except:
                        pass
        
        # 计算持仓
        for coin in coins_to_fetch:
            amount = balance['total'][coin]
            symbol = f"{coin}/USDT"
            
            if symbol in tickers:
                ticker = tickers[symbol]
                # 安全检查：确保 ticker['last'] 不是 None
                if ticker.get('last') is None:
                    logger.warning(f"⚠️ {symbol} 价格为 None，跳过")
                    continue
                
                value = amount * ticker['last']
                if value > 1:  # 过滤小额持仓
                    change = ticker.get('percentage', 0)
                    if change is None:
                        change = 0
                    emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
                    positions.append({
                        'coin': coin,
                        'amount': amount,
                        'value': value,
                        'price': ticker['last'],
                        'change': change,
                        'emoji': emoji
                    })
                    total_value += value
            else:
                # 无法获取价格的币种
                logger.debug(f"未找到 {symbol} 的价格信息")
                positions.append({
                    'coin': coin,
                    'amount': amount,
                    'value': 0,
                    'price': 0,
                    'change': 0,
                    'emoji': '⚪'
                })
        
        # 排序：按价值降序
        positions.sort(key=lambda x: x['value'], reverse=True)
        
        total_time = time.time() - start_time
        logger.info(f"⏱️ 账户查询总耗时: {total_time:.2f}s")
        
        report = (
            f"💼 **账户资产摘要**\n"
            f"{'═' * 35}\n\n"
            f"💰 **总估值**: ${total_value:,.2f} USDT\n"
            f"💵 **可用USDT**: ${free_usdt:,.2f}\n"
            f"📊 **今日已交易**: ${get_daily_traded_amount():,.2f} / ${_get_daily_trade_limit():,.0f}\n\n"
        )
        
        if positions:
            report += "📦 **持仓明细**:\n"
            for p in positions:
                pct = (p['value'] / total_value * 100) if total_value > 0 else 0
                report += f"  {p['emoji']} **{p['coin']}**: {p['amount']:.6f}\n"
                report += f"     价值: ${p['value']:.2f} ({pct:.1f}%)\n"
                if p['price'] > 0:
                    report += f"     价格: ${p['price']:,.2f} ({'+' if p['change'] >= 0 else ''}{p['change']:.2f}%)\n"
        else:
            report += "📦 **持仓**: (无)\n"
        
        return report
    except Exception as e:
        logger.error(f"获取账户失败: {e}")
        return f"❌ 获取失败: {str(e)}"

@mcp.tool()
@mcp_tool_safe
def get_open_orders(symbol: str = None) -> str:
    """
    获取当前挂单列表（修复版：避免速率限制警告）。
    Args:
        symbol: 可选的交易对，如 BTC/USDT。不指定则查询所有白名单币种。
    """
    try:
        exchange = get_exchange()
        
        # 抑制警告
        if 'warnOnFetchOpenOrdersWithoutSymbol' not in exchange.options:
            exchange.options['warnOnFetchOpenOrdersWithoutSymbol'] = False
        
        orders = []
        
        if symbol:
            # 查询单个交易对
            logger.debug(f"查询 {symbol} 挂单...")
            orders = exchange.fetch_open_orders(symbol)
        else:
            # 遍历白名单查询（避免速率限制）
            logger.debug(f"查询所有白名单币种挂单...")
            for sym in sorted(_get_allowed_symbols()):
                try:
                    sym_orders = exchange.fetch_open_orders(sym)
                    orders.extend(sym_orders)
                except Exception as e:
                    logger.debug(f"跳过 {sym}: {e}")
                    continue
        
        if not orders:
            return "📋 **当前无挂单**"
        
        report = f"📋 **当前挂单** ({len(orders)} 笔)\n" + "─" * 30 + "\n\n"
        
        for order in orders:
            side_emoji = "🟢" if order['side'] == 'buy' else "🔴"
            report += f"{side_emoji} **{order['symbol']}** - {order['side'].upper()}\n"
            report += f"   数量: {order['amount']} | 价格: ${order['price']}\n"
            order_id = str(order['id'])
            report += f"   ID: {order_id[:12]}{'...' if len(order_id) > 12 else ''}\n\n"
        
        return report
    except Exception as e:
        logger.error(f"获取挂单失败: {e}")
        return f"❌ 获取失败: {str(e)}"

@mcp.tool()
@mcp_tool_safe
def cancel_order(order_id: str, symbol: str) -> str:
    """
    取消指定订单。
    Args:
        order_id: 订单ID
        symbol: 交易对 (如 BTC/USDT)
    """
    try:
        exchange = get_exchange()
        exchange.cancel_order(order_id, symbol)
        logger.info(f"🗑️ 订单已取消: {order_id}")
        return f"✅ 订单 {order_id} 已取消"
    except Exception as e:
        return f"❌ 取消失败: {str(e)}"

# ============================================
# 6. 交易执行系统
# ============================================

@mcp.tool()
@mcp_tool_safe
def place_order(symbol: str, side: str, amount: float, price: float = None, order_type: str = "market") -> str:
    """
    下单交易。
    Args:
        symbol: 交易对 (如 BTC/USDT)
        side: 买卖方向 (buy/sell)
        amount: 交易数量
        price: 限价单价格 (可选)
        order_type: 订单类型 (market/limit)
    """
    try:
        exchange = get_exchange()
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        exec_price = price if (order_type == 'limit' and price) else current_price
        cost = amount * exec_price
        
        # 风控检查
        max_trade_amount = _get_max_trade_amount()
        if cost > max_trade_amount:
            return f"❌ 单笔交易超过限额 {max_trade_amount} USDT (当前: {cost:.2f})"

        # 学习模块：下单纪律拦截（可选）
        try:
            from learning.discipline import evaluate_order
            allowed, reason = evaluate_order(symbol=symbol, side=side, estimated_cost=float(cost))
            if not allowed:
                return reason
        except Exception:
            pass
        
        # 执行订单
        if order_type == 'limit' and price:
            order = exchange.create_order(symbol, 'limit', side, amount, price)
        else:
            order = exchange.create_order(symbol, 'market', side, amount)
        
        # 记录交易
        log_trade(order['id'], symbol, side, amount, exec_price, f"{cost:.2f}", order['status'])
        
        logger.info(f"🚀 下单成功: {side.upper()} {symbol} {amount}")
        
        return (
            f"🚀 **下单成功**\n"
            f"{'─' * 25}\n"
            f"📋 订单ID: {order['id']}\n"
            f"💹 交易对: {symbol}\n"
            f"{'📈' if side.lower() == 'buy' else '📉'} 方向: {side.upper()}\n"
            f"📊 数量: {amount}\n"
            f"💰 价格: ${exec_price:,.2f}\n"
            f"💵 总额: {cost:.2f} USDT\n"
            f"📌 状态: {order['status']}"
        )
    except Exception as e:
        logger.error(f"下单失败: {e}")
        return f"❌ 下单失败: {str(e)}"

@mcp.tool()
@mcp_tool_safe
def calculate_position_size(account_balance: float, entry_price: float, stop_loss: float, risk_percent: float = 1.0) -> str:
    """
    根据风险管理计算建议仓位。
    Args:
        account_balance: 账户总资金 (USDT)
        entry_price: 入场价格
        stop_loss: 止损价格
        risk_percent: 风险比例 (默认 1%)
    """
    try:
        if entry_price <= 0 or stop_loss <= 0:
            return "❌ 价格必须大于0"
        if entry_price == stop_loss:
            return "❌ 入场价不能等于止损价"
        
        risk_amount = account_balance * (risk_percent / 100)
        price_diff = abs(entry_price - stop_loss)
        position_size = risk_amount / price_diff
        position_value = position_size * entry_price
        
        # 是否做多/做空
        direction = "做多" if entry_price > stop_loss else "做空"
        risk_reward_1_2 = entry_price + (entry_price - stop_loss) * 2 if direction == "做多" else entry_price - (stop_loss - entry_price) * 2
        
        return (
            f"🛡️ **风险管理建议**\n"
            f"{'─' * 25}\n"
            f"📊 方向: {direction}\n"
            f"💰 风险金额: ${risk_amount:.2f} ({risk_percent}%)\n"
            f"📏 建议仓位: {position_size:.6f}\n"
            f"💵 仓位价值: ${position_value:.2f}\n\n"
            f"**止盈参考** (1:2 风险回报):\n"
            f"🎯 止盈价: ${risk_reward_1_2:,.2f}\n"
            f"🛑 止损价: ${stop_loss:,.2f}"
        )
    except Exception as e:
        return f"❌ 计算错误: {str(e)}"

# ============================================
# 7. 自动交易策略
# ============================================

@mcp.tool()
@mcp_tool_safe
def execute_strategy(symbol: str, strategy: str, amount: float) -> str:
    """
    执行自动交易策略。
    Args:
        symbol: 交易对 (如 BTC/USDT)
        strategy: 策略类型 (RSI_Oversold, RSI_Overbought, MA_Crossover, BB_Breakout)
        amount: 交易数量
    """
    try:
        if symbol not in _get_allowed_symbols():
            return f"❌ {symbol} 不在白名单"
        
        exchange = get_exchange()
        ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=OHLCV_LIMIT_STRATEGY)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = calculate_indicators(df)
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        signal = None
        reason = ""
        
        if strategy == "RSI_Oversold":
            # RSI < 30 买入
            if curr['RSI'] < 30:
                signal, reason = "buy", f"RSI 超卖 ({curr['RSI']:.1f} < 30)"
            else:
                return f"⏸️ 策略未触发\nRSI 当前: {curr['RSI']:.1f} (需 < 30)"
        
        elif strategy == "RSI_Overbought":
            # RSI > 70 卖出
            if curr['RSI'] > 70:
                signal, reason = "sell", f"RSI 超买 ({curr['RSI']:.1f} > 70)"
            else:
                return f"⏸️ 策略未触发\nRSI 当前: {curr['RSI']:.1f} (需 > 70)"
        
        elif strategy == "MA_Crossover":
            # 金叉做多，死叉做空
            if prev['SMA_20'] <= prev['SMA_50'] and curr['SMA_20'] > curr['SMA_50']:
                signal, reason = "buy", "均线金叉 (SMA20 上穿 SMA50)"
            elif prev['SMA_20'] >= prev['SMA_50'] and curr['SMA_20'] < curr['SMA_50']:
                signal, reason = "sell", "均线死叉 (SMA20 下穿 SMA50)"
            else:
                return f"⏸️ 策略未触发\nSMA20: {curr['SMA_20']:.2f} | SMA50: {curr['SMA_50']:.2f}"
        
        elif strategy == "BB_Breakout":
            # 突破布林带上轨卖出，跌破下轨买入
            if curr['close'] < curr['BB_Lower']:
                signal, reason = "buy", f"跌破布林带下轨 (${curr['BB_Lower']:.2f})"
            elif curr['close'] > curr['BB_Upper']:
                signal, reason = "sell", f"突破布林带上轨 (${curr['BB_Upper']:.2f})"
            else:
                return f"⏸️ 策略未触发\n价格在布林带内 (${curr['BB_Lower']:.2f} - ${curr['BB_Upper']:.2f})"
        
        else:
            strategies = ["RSI_Oversold", "RSI_Overbought", "MA_Crossover", "BB_Breakout"]
            return f"❌ 未知策略: {strategy}\n可用策略: {', '.join(strategies)}"
        
        if signal:
            result = place_order(symbol, signal, amount)
            return f"{result}\n\n💡 **触发原因**: {reason}"
        
        return "⏸️ 策略未触发"
    
    except Exception as e:
        logger.error(f"策略执行失败: {e}")
        return f"❌ 策略错误: {str(e)}"

@mcp.tool()
@mcp_tool_safe
def get_available_strategies() -> str:
    """获取可用的自动交易策略列表"""
    return """
🤖 **可用自动交易策略**
═══════════════════════════

**RSI_Oversold** (超卖买入)
  触发条件: RSI < 30
  操作: 买入
  适用: 逆向投资，抄底

**RSI_Overbought** (超买卖出)
  触发条件: RSI > 70
  操作: 卖出
  适用: 获利了结，止盈

**MA_Crossover** (均线交叉)
  触发条件: SMA20 与 SMA50 交叉
  操作: 金叉买入 / 死叉卖出
  适用: 趋势跟踪

**BB_Breakout** (布林带突破)
  触发条件: 价格突破布林带
  操作: 下轨买入 / 上轨卖出
  适用: 波动交易

───────────────────────────
💡 使用示例:
execute_strategy("BTC/USDT", "RSI_Oversold", 0.001)
"""

# ============================================
# 8. 日志系统
# ============================================

@mcp.tool()
@mcp_tool_safe
def get_server_logs(lines: int = 30) -> str:
    """
    获取服务器运行日志。
    Args:
        lines: 显示最近多少行
    """
    if not os.path.exists(LOG_FILE):
        return "📭 暂无日志"
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent = all_lines[-lines:]
            return "📋 **服务器日志**\n" + "─" * 30 + "\n\n" + "".join(recent)
    except Exception as e:
        return f"❌ 读取失败: {str(e)}"

@mcp.tool()
@mcp_tool_safe
def get_system_status() -> str:
    """获取系统状态和配置信息"""
    use_testnet = os.getenv("USE_TESTNET", "True").lower() == "true"
    email_enabled = os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "False").lower() == "true"
    
    try:
        exchange = get_exchange()
        connected = True
    except:
        connected = False
    
    return (
        f"⚙️ **系统状态**\n"
        f"{'═' * 30}\n\n"
        f"🌐 **网络**: {'🟢 Testnet' if use_testnet else '🔴 Mainnet'}\n"
        f"📡 **连接**: {'✅ 正常' if connected else '❌ 断开'}\n"
        f"📧 **邮件**: {'✅ 已启用' if email_enabled else '❌ 未启用'}\n\n"
        f"**优化功能 (P0/P1)**\n"
        f"├─ stdout隔离: ✅ 启用\n"
        f"├─ 异常保护: ✅ 启用\n"
        f"├─ 智能日志: {'✅ 启用' if USE_SMART_LOGGER else '❌ 禁用'}\n"
        f"└─ 智能缓存: {'✅ 启用' if USE_SMART_CACHE else '❌ 禁用'}\n\n"
        f"**交易限制**\n"
        f"├─ 单笔限额: ${_get_max_trade_amount():,.0f}\n"
        f"├─ 每日限额: ${_get_daily_trade_limit():,.0f}\n"
        f"└─ 白名单币种: {len(_get_allowed_symbols())} 个\n\n"
        f"**通知开关**\n"
        f"├─ 交易执行: {'✅' if _notify_enabled('NOTIFY_TRADE_EXECUTION', True) else '❌'}\n"
        f"├─ 价格预警: {'✅' if _notify_enabled('NOTIFY_PRICE_ALERTS', True) else '❌'}\n"
        f"├─ 日报/报告: {'✅' if _notify_enabled('NOTIFY_DAILY_REPORT', True) else '❌'}\n"
        f"└─ 系统错误: {'✅' if _notify_enabled('NOTIFY_SYSTEM_ERRORS', True) else '❌'}\n\n"
        f"**文件路径**\n"
        f"├─ 日志: {LOG_FILE}\n"
        f"└─ 交易记录: {TRADE_LOG_FILE}"
    )


@mcp.tool()
@mcp_tool_safe
def generate_analysis_report(
    symbol: str = "BTC/USDT",
    mode: str = "simple",
    timeframe: str = "1h",
    include_sections: str = "ai_advice,technical,sentiment,signals,position,market_overview",
    save_local: bool = True,
    send_email_report: bool = False,
    report_title: str = "",
) -> str:
    """
    生成分析报告（可保存本地，并可选择发送到邮箱）。
    Args:
        symbol: 交易对
        mode: AI 分析模式 (simple/professional)
        timeframe: 技术分析周期
        include_sections: 需要包含的章节，逗号分隔
        save_local: 是否保存到本地 reports/ 目录
        send_email_report: 是否将报告内容作为邮件正文发送
        report_title: 自定义标题（可空）
    """
    created_at = datetime.now()
    date_str = created_at.strftime('%Y%m%d')
    ts_str = created_at.strftime('%Y%m%d_%H%M%S')

    symbol_safe = _safe_filename_component(symbol)
    mode_safe = _safe_filename_component(mode)
    tf_safe = _safe_filename_component(timeframe)
    out_dir = _ensure_reports_dir(date_str)

    sections = [s.strip().lower() for s in (include_sections or '').split(',') if s.strip()]
    if not sections:
        sections = ["ai_advice", "technical", "sentiment"]

    title = (report_title or f"Heablcoin 分析报告 - {symbol} - {mode} - {timeframe}").strip()

    content_parts: List[str] = []
    content_parts.append(f"# {title}\n")
    content_parts.append(f"- 时间: {created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
    content_parts.append(f"- 交易对: {symbol}\n")
    content_parts.append(f"- 模式: {mode}\n")
    content_parts.append(f"- 周期: {timeframe}\n")
    content_parts.append("\n---\n")

    results: Dict[str, str] = {}
    errors: Dict[str, str] = {}

    def _run(name: str, fn):
        try:
            results[name] = fn()
        except Exception as e:
            msg = f"{type(e).__name__}: {e}"
            errors[name] = msg
            logger.error(f"报告生成失败[{name}]: {msg}")

    if "ai_advice" in sections:
        _run("ai_advice", lambda: get_ai_trading_advice(symbol, mode))
    if "technical" in sections:
        _run("technical", lambda: get_comprehensive_analysis(symbol, timeframe))
    if "sentiment" in sections:
        _run("sentiment", lambda: get_market_sentiment(symbol))
    if "signals" in sections:
        _run("signals", lambda: get_trading_signals(symbol))
    if "position" in sections:
        _run("position", lambda: get_position_recommendation(symbol, None, "moderate"))
    if "market_overview" in sections:
        _run("market_overview", lambda: get_market_overview("simple" if mode.lower() == "simple" else "professional"))

    def _append_section(heading: str, key: str):
        if key in results:
            content_parts.append(f"\n## {heading}\n\n")
            content_parts.append(results[key].strip() + "\n")
        elif key in errors:
            content_parts.append(f"\n## {heading}\n\n")
            content_parts.append(f"❌ 生成失败: {errors[key]}\n")

    _append_section("AI 交易建议", "ai_advice")
    _append_section("综合技术分析", "technical")
    _append_section("市场情绪", "sentiment")
    _append_section("交易信号汇总", "signals")
    _append_section("仓位建议", "position")
    _append_section("市场全景", "market_overview")

    report_md = "".join(content_parts).strip() + "\n"

    saved_md_path = ""
    saved_meta_path = ""
    if save_local:
        base_name = f"{ts_str}__{symbol_safe}__{mode_safe}__{tf_safe}"
        saved_md_path = os.path.join(out_dir, base_name + ".md")
        saved_meta_path = os.path.join(out_dir, base_name + ".meta.json")

        meta = {
            "title": title,
            "created_at": created_at.isoformat(),
            "symbol": symbol,
            "mode": mode,
            "timeframe": timeframe,
            "include_sections": sections,
            "paths": {"markdown": saved_md_path, "meta": saved_meta_path},
            "email": {"requested": bool(send_email_report), "enabled": os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "False")},
            "errors": errors,
        }

        _write_text(saved_md_path, report_md)
        _write_json(saved_meta_path, meta)

    email_status = "未发送"
    if send_email_report:
        html = (
            f"<html><body style='font-family: Arial; padding: 16px;'>"
            f"<h2>{title}</h2>"
            f"<p><b>时间</b>: {created_at.strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            f"<b>交易对</b>: {symbol}<br/>"
            f"<b>模式</b>: {mode}<br/>"
            f"<b>周期</b>: {timeframe}</p>"
            f"<hr/>"
            f"<pre style='white-space: pre-wrap; word-wrap: break-word;'>{report_md}</pre>"
            f"<hr/><small>🤖 Heablcoin 智能交易系统</small>"
            f"</body></html>"
        )
        ok = send_email(title, html, msg_type='REPORT')
        email_status = "✅ 已发送" if ok else "❌ 发送失败"

    summary_lines = []
    summary_lines.append(f"✅ 报告已生成: {title}")
    summary_lines.append(f"📁 保存: {'是' if save_local else '否'}")
    if save_local:
        summary_lines.append(f"- Markdown: {saved_md_path}")
        summary_lines.append(f"- Meta: {saved_meta_path}")
    summary_lines.append(f"📧 邮件: {email_status}")
    if errors:
        summary_lines.append(f"⚠️ 部分章节失败: {', '.join(sorted(errors.keys()))}")
    return "\n".join(summary_lines)


# ============================================
# 9. 性能与缓存监控工具（P1新增）
# ============================================

@mcp.tool()
@mcp_tool_safe
def get_cache_stats() -> str:
    """获取缓存系统统计信息"""
    if not USE_SMART_CACHE or smart_cache is None:
        return "❌ 缓存系统未启用"
    
    try:
        stats = smart_cache.get_stats()
        
        report = (
            f"📊 **缓存统计**\n"
            f"{'═' * 30}\n\n"
            f"**性能指标**\n"
            f"├─ 命中率: {stats['hit_rate']}\n"
            f"├─ 总命中: {stats['total_hits']}\n"
            f"├─ 总未命中: {stats['total_misses']}\n"
            f"├─ 缓存键数: {stats['total_keys']}\n"
            f"└─ 缓存大小: {stats['cache_size_bytes'] / 1024:.1f} KB\n\n"
        )
        
        if stats['top_hits']:
            report += "**TOP 10 热门缓存**\n"
            for item in stats['top_hits']:
                report += f"├─ {item['key']}: {item['hits']} 次\n"
        
        return report
    except Exception as e:
        return f"❌ 获取统计失败: {str(e)}"


@mcp.tool()
@mcp_tool_safe
def get_performance_stats() -> str:
    """获取性能统计信息"""
    if not USE_SMART_LOGGER or smart_logger is None:
        return "❌ 智能日志系统未启用"
    
    try:
        stats = smart_logger.get_performance_stats()
        
        if not stats:
            return "📊 暂无性能数据"
        
        # 按平均时间排序
        sorted_stats = sorted(
            stats.items(),
            key=lambda x: x[1]['total_time'] / x[1]['total_calls'],
            reverse=True
        )[:10]
        
        report = (
            f"⚡ **性能统计 (TOP 10 慢函数)**\n"
            f"{'═' * 40}\n\n"
        )
        
        for func_name, data in sorted_stats:
            avg_time = data['total_time'] / data['total_calls']
            report += (
                f"**{func_name}**\n"
                f"├─ 调用次数: {data['total_calls']}\n"
                f"├─ 平均耗时: {avg_time:.2f}s\n"
                f"├─ 最大耗时: {data['max_time']:.2f}s\n"
                f"└─ 错误次数: {data['errors']}\n\n"
            )
        
        return report
    except Exception as e:
        return f"❌ 获取统计失败: {str(e)}"


@mcp.tool()
@mcp_tool_safe
def clear_cache(pattern: str = None) -> str:
    """
    清除缓存
    Args:
        pattern: 可选的匹配模式，只清除包含该模式的缓存键
    """
    if not USE_SMART_CACHE or smart_cache is None:
        return "❌ 缓存系统未启用"
    
    try:
        smart_cache.clear(pattern)
        if pattern:
            return f"✅ 已清除匹配 '{pattern}' 的缓存"
        else:
            return "✅ 已清除所有缓存"
    except Exception as e:
        return f"❌ 清除失败: {str(e)}"


# ============================================
# 启动入口
# ============================================

if __name__ == "__main__":
    logger.info("🚀 Heablcoin MCP Server 已启动")
    logger.info("📝 GitHub: Heablcoin")
    mcp.run()
