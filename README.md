# 小红书 MCP Python 项目

这是一个基于 Model Context Protocol (MCP) 的小红书自动化工具，提供登录、状态检查和内容发布功能。

## 功能特性

- 登录功能 - 支持扫码登录小红书账号
- 状态检查 - 快速检查当前登录状态
- 内容发布 - 自动发布图文内容到小红书
- MCP 集成 - 完整的 MCP 服务器实现，可与 AI 助手集成

## 安装要求

- Python >= 3.10
- 已安装 Chrome 浏览器
- uv 包管理器（推荐）

## 快速开始

### 安装依赖

```bash
# 使用 uv 安装（推荐）
uv sync

# 或使用 pip
pip install -e .
```

### 安装 Playwright 浏览器

```bash
uv run playwright install chromium
```

### 最简单启动（开发模式）

```bash
uv run mcp dev src/xiaohongshu_mcp/server.py
```

等价的生产脚本启动方式：

```bash
uv run xiaohongshu-mcp-server
```

## 使用方式

### 方式一：独立命令行工具

#### 1. 登录小红书

```bash
# 使用有界面模式登录（推荐）
uv run xiaohongshu-login

# 使用无头模式登录
uv run xiaohongshu-login --headless
```

#### 2. 检查登录状态

```bash
uv run xiaohongshu-status
```

#### 3. 发布内容

```bash
uv run xiaohongshu-publish \
  --title "我的标题" \
  --content "这是正文内容" \
  --images "image1.jpg" "image2.png"
```

### 方式二：MCP 服务器

启动 MCP 服务器，可与支持 MCP 协议的 AI 助手集成：

```bash
# 启动开发模式 MCP 服务器
uv run mcp dev src/xiaohongshu_mcp/server.py

# 或使用脚本启动
uv run xiaohongshu-mcp-server
```

#### MCP 工具说明

服务器提供三个 MCP 工具：

1. **xiaohongshu_login** - 登录小红书账号
   - headless: bool - 是否使用无头模式（默认：False）
   - chrome_path: str - Chrome 路径（可选）

2. **xiaohongshu_check_status** - 检查登录状态
   - headless: bool - 是否使用无头模式（默认：True）
   - chrome_path: str - Chrome 路径（可选）

3. **xiaohongshu_publish** - 发布内容
   - title: str - 标题（必填，<=40字符）
   - content: str - 正文内容（必填）
   - image_paths: List[str] - 图片路径列表（必填）
   - headless: bool - 是否使用无头模式（默认：False）
   - chrome_path: str - Chrome 路径（可选）

## 配置说明

### 登录状态保存

登录状态通过 cookies 保存在：
```
~/.xiaohongshu_mcp/cookies.json
```

### 日志配置

MCP 服务器日志保存在：
```
logs/mcp_server.log
```

### 支持的图片格式

- JPG/JPEG
- PNG
- GIF
- WebP

## 开发与测试

### 项目结构

```
src/xiaohongshu_mcp/
├── browser/              # 浏览器管理模块
│   ├── cookies.py       # Cookie 管理
│   └── driver.py        # 浏览器驱动
├── xiaohongshu/         # 小红书功能模块
│   ├── login.py         # 登录功能
│   └── publish.py       # 发布功能
├── server.py            # MCP 服务器
├── login.py             # 登录命令行工具
├── check_status.py      # 状态检查工具
└── publish.py           # 发布命令行工具
```

## 注意事项

- 发布功能建议使用有界面模式，便于观察发布过程
- 首次使用需要扫码登录
- 图片文件必须存在且格式正确
- 标题长度不能超过 40 个字符

## 故障排除

### 常见问题

1. **登录失败**
   - 确保网络连接正常
   - 尝试清除 cookies 后重新登录
   - 检查 Chrome 浏览器是否正常安装

2. **发布失败**
   - 确认已登录状态
   - 检查图片文件路径和格式
   - 验证标题和内容长度

3. **MCP 服务器启动失败**
   - 确保安装了 mcp[cli] 依赖
   - 检查日志文件查看详细错误信息

## 技术栈

- **Python 3.10+** - 主要开发语言
- **Playwright** - 浏览器自动化
- **MCP Python SDK** - Model Context Protocol 支持
- **Loguru** - 日志管理
- **Pydantic** - 数据验证
- **uv** - 包管理器

## 许可证

本项目基于 MIT 许可证开源。
