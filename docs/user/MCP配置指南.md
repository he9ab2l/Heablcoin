# Heablcoin MCP 配置指南

## 问题诊断

如果 Claude Desktop 或 Windsurf 无法导入 Heablcoin MCP 服务器，请按以下步骤检查和配置。

---

## 1. Claude Desktop 配置

### 配置文件位置
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### 配置内容

```json
{
  "mcpServers": {
    "heablcoin": {
      "command": "python",
      "args": ["d:\\MCP\\Heablcoin.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

**重要提示**:
- ✅ 使用**绝对路径** `d:\\MCP\\Heablcoin.py`
- ✅ Windows 路径使用双反斜杠 `\\` 或单正斜杠 `/`
- ✅ 确保 `python` 命令在 PATH 中可用
- ✅ 配置后需要**完全重启** Claude Desktop

### 手动创建配置文件

如果配置文件不存在，请手动创建：

**Windows PowerShell**:
```powershell
# 创建目录
New-Item -ItemType Directory -Force -Path "$env:APPDATA\Claude"

# 创建配置文件
@"
{
  "mcpServers": {
    "heablcoin": {
      "command": "python",
      "args": ["d:\\MCP\\Heablcoin.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      }
    }
  }
}
"@ | Out-File -FilePath "$env:APPDATA\Claude\claude_desktop_config.json" -Encoding UTF8
```

---

## 2. Windsurf 配置

### 配置文件位置
- **Windows**: `%APPDATA%\Windsurf\mcp_config.json`
- **macOS**: `~/Library/Application Support/Windsurf/mcp_config.json`
- **Linux**: `~/.config/Windsurf/mcp_config.json`

### 配置内容

```json
{
  "mcpServers": {
    "heablcoin": {
      "command": "python",
      "args": ["d:/MCP/Heablcoin.py"],
      "disabled": false,
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

**重要提示**:
- ✅ 使用**绝对路径** `d:/MCP/Heablcoin.py`
- ✅ Windsurf 推荐使用正斜杠 `/`
- ✅ 设置 `"disabled": false` 启用服务器
- ✅ 配置后需要**重启** Windsurf 或重新加载 MCP

### 手动创建配置文件

**Windows PowerShell**:
```powershell
# 创建目录
New-Item -ItemType Directory -Force -Path "$env:APPDATA\Windsurf"

# 创建配置文件
@"
{
  "mcpServers": {
    "heablcoin": {
      "command": "python",
      "args": ["d:/MCP/Heablcoin.py"],
      "disabled": false,
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      }
    }
  }
}
"@ | Out-File -FilePath "$env:APPDATA\Windsurf\mcp_config.json" -Encoding UTF8
```

---

## 3. 常见问题排查

### 问题 1: Python 命令找不到

**症状**: 配置后无法启动，提示找不到 python

**解决方案**:
```powershell
# 检查 Python 路径
where.exe python

# 如果找不到，使用完整路径
# 例如: "C:\\Users\\YourName\\anaconda3\\python.exe"
```

**修改配置**:
```json
{
  "mcpServers": {
    "heablcoin": {
      "command": "C:\\Users\\YourName\\anaconda3\\python.exe",
      "args": ["d:\\MCP\\Heablcoin.py"]
    }
  }
}
```

### 问题 2: 路径错误

**症状**: 提示找不到 Heablcoin.py 文件

**解决方案**:
```powershell
# 检查文件是否存在
Test-Path "d:\MCP\Heablcoin.py"

# 获取绝对路径
(Get-Item "d:\MCP\Heablcoin.py").FullName
```

### 问题 3: 编码问题

**症状**: 中文乱码或输出异常

**解决方案**: 确保配置中包含编码设置
```json
"env": {
  "PYTHONIOENCODING": "utf-8",
  "PYTHONUTF8": "1"
}
```

### 问题 4: 依赖缺失

**症状**: 启动失败，提示 ModuleNotFoundError

**解决方案**:
```bash
# 检查依赖
pip list | findstr mcp
pip list | findstr ccxt

# 重新安装依赖
pip install -r requirements.txt
```

### 问题 5: 环境变量未配置

**症状**: 提示缺少 API Key 或配置

**解决方案**:
```bash
# 检查 .env 文件
cat .env

# 确保包含必要配置
BINANCE_API_KEY=your_key
BINANCE_SECRET_KEY=your_secret
```

---

## 4. 验证配置

### 测试 MCP 服务器

```bash
# 进入项目目录
cd d:\MCP

# 直接运行测试
python Heablcoin.py

# 如果正常，应该看到 JSON-RPC 初始化信息
# 按 Ctrl+C 退出
```

### 测试功能

```bash
# 运行快速测试
python Heablcoin-test.py --quick

# 运行完整测试
python Heablcoin-test.py --self-check
```

---

## 5. 重启应用

配置完成后，**必须完全重启**应用才能生效：

### Claude Desktop
1. 完全退出 Claude Desktop（任务管理器确认进程已关闭）
2. 重新启动 Claude Desktop
3. 在对话中输入: "列出可用的 MCP 工具"
4. 应该能看到 Heablcoin 的工具列表

### Windsurf
1. 关闭 Windsurf
2. 重新启动 Windsurf
3. 打开命令面板，搜索 "MCP"
4. 查看 MCP 服务器状态

---

## 6. 查看日志

如果仍然无法工作，检查日志文件：

```powershell
# Heablcoin 日志
Get-Content "d:\MCP\logs\heablcoin.log" -Tail 50

# Claude Desktop 日志 (Windows)
Get-Content "$env:APPDATA\Claude\logs\mcp*.log" -Tail 50

# Windsurf 日志
# 查看 Windsurf 的开发者工具控制台
```

---

## 7. 完整配置示例

### 多个 MCP 服务器配置

```json
{
  "mcpServers": {
    "heablcoin": {
      "command": "python",
      "args": ["d:\\MCP\\Heablcoin.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      }
    },
    "other-server": {
      "command": "node",
      "args": ["path/to/other-server.js"]
    }
  }
}
```

---

## 8. 快速配置脚本

### Windows 一键配置

保存为 `setup_mcp.ps1`:

```powershell
# Heablcoin MCP 一键配置脚本

$projectPath = "d:\MCP"
$pythonCmd = (Get-Command python -ErrorAction SilentlyContinue).Source

if (-not $pythonCmd) {
    Write-Host "❌ 找不到 Python，请先安装 Python" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Python 路径: $pythonCmd" -ForegroundColor Green

# Claude Desktop 配置
$claudeDir = "$env:APPDATA\Claude"
$claudeConfig = "$claudeDir\claude_desktop_config.json"

if (-not (Test-Path $claudeDir)) {
    New-Item -ItemType Directory -Force -Path $claudeDir | Out-Null
}

$config = @{
    mcpServers = @{
        heablcoin = @{
            command = "python"
            args = @("$projectPath\Heablcoin.py")
            env = @{
                PYTHONIOENCODING = "utf-8"
                PYTHONUTF8 = "1"
            }
        }
    }
}

$config | ConvertTo-Json -Depth 10 | Out-File -FilePath $claudeConfig -Encoding UTF8
Write-Host "✅ Claude Desktop 配置已创建: $claudeConfig" -ForegroundColor Green

# Windsurf 配置
$windsurfDir = "$env:APPDATA\Windsurf"
$windsurfConfig = "$windsurfDir\mcp_config.json"

if (-not (Test-Path $windsurfDir)) {
    New-Item -ItemType Directory -Force -Path $windsurfDir | Out-Null
}

$config.mcpServers.heablcoin.disabled = $false
$config.mcpServers.heablcoin.args = @("$projectPath/Heablcoin.py")

$config | ConvertTo-Json -Depth 10 | Out-File -FilePath $windsurfConfig -Encoding UTF8
Write-Host "✅ Windsurf 配置已创建: $windsurfConfig" -ForegroundColor Green

Write-Host "`n📝 配置完成！请重启 Claude Desktop 或 Windsurf" -ForegroundColor Cyan
Write-Host "📝 测试命令: python $projectPath\Heablcoin-test.py --quick" -ForegroundColor Cyan
```

运行脚本:
```powershell
powershell -ExecutionPolicy Bypass -File setup_mcp.ps1
```

---

## 9. 联系支持

如果以上方法都无法解决问题，请提供以下信息：

1. 操作系统版本
2. Python 版本 (`python --version`)
3. MCP 库版本 (`pip show mcp`)
4. 配置文件内容
5. 错误日志

---

**配置成功后，你就可以在 Claude 或 Windsurf 中使用 Heablcoin 的所有功能了！** 🎉
