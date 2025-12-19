# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-12-19

### Added
- **Core MCP Server**: Implemented `Heablcoin.py` as the main entry point compatible with MCP protocol.
- **Market Analysis**: Modular analysis tools including technical indicators, sentiment analysis, and trading signals.
- **Trading Execution**: Support for Binance (testnet/mainnet) with safety checks via `exchange_adapter`.
- **Cloud Integration**: Redis-backed task queue (`qinglong_worker`), webhooks, and asynchronous task execution.
- **Personal Analytics**: Tools for performance tracking, portfolio analysis, and trade journaling.
- **Reporting**: PDF/Markdown report generation and flexible email notification system.
- **Governance & Risk**: Risk budget management, circuit breakers, and strategy registry.
- **Documentation**: Comprehensive guides in `docs/` covering installation, configuration, and API usage.
- **Testing**: Unified test runner `tests/run_tests.py` for unit and integration tests.

### Security
- Environment variable management via `.env`.
- Hardcoded sensitive paths removed from documentation.
