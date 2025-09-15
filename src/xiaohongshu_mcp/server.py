"""小红书MCP服务器"""

import asyncio
from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from loguru import logger

from xiaohongshu_mcp.browser.driver import BrowserManager
from xiaohongshu_mcp.xiaohongshu.login import XiaohongshuLogin
from xiaohongshu_mcp.xiaohongshu.publish import XiaohongshuPublish


# 创建MCP服务器
mcp = FastMCP("xiaohongshu-mcp")

@mcp.tool()
async def xiaohongshu_login(
    headless: bool = False,
    chrome_path: Optional[str] = None
) -> str:
    """
    登录小红书账号

    Args:
        headless: 是否使用无头模式，默认False（建议使用有界面模式进行扫码）
        chrome_path: Chrome浏览器可执行文件路径，可选

    Returns:
        登录结果消息
    """
    try:
        logger.info("开始小红书登录流程...")

        # 创建浏览器管理器
        browser_manager = BrowserManager(
            headless=headless,
            chrome_path=chrome_path
        )

        async with browser_manager.get_page() as page:
            # 创建登录处理器
            login_handler = XiaohongshuLogin(page)

            # 执行登录
            success = await login_handler.login()

            if success:
                logger.success("🎉 登录成功！")
                return "✅ 小红书登录成功"
            else:
                logger.error("❌ 登录失败")
                return "❌ 小红书登录失败"

    except Exception as e:
        error_msg = f"登录过程中发生错误: {e}"
        logger.error(error_msg)
        return f"❌ {error_msg}"


@mcp.tool()
async def xiaohongshu_check_status(
    headless: bool = True,
    chrome_path: Optional[str] = None
) -> str:
    """
    检查小红书登录状态

    Args:
        headless: 是否使用无头模式，默认True（状态检查可使用无头模式）
        chrome_path: Chrome浏览器可执行文件路径，可选

    Returns:
        登录状态信息
    """
    try:
        logger.info("检查小红书登录状态...")

        # 创建浏览器管理器
        browser_manager = BrowserManager(
            headless=headless,
            chrome_path=chrome_path
        )

        async with browser_manager.get_page() as page:
            # 创建登录处理器
            login_handler = XiaohongshuLogin(page)

            # 检查登录状态
            is_logged_in = await login_handler.check_login_status()

            if is_logged_in:
                logger.success("✅ 已登录")
                return "✅ 小红书已登录"
            else:
                logger.info("❌ 未登录")
                return "❌ 小红书未登录，请先执行登录操作"

    except Exception as e:
        error_msg = f"检查登录状态时发生错误: {e}"
        logger.error(error_msg)
        return f"❌ {error_msg}"


@mcp.tool()
async def xiaohongshu_publish(
    title: str,
    content: str,
    image_paths: List[str],
    headless: bool = False,
    chrome_path: Optional[str] = None
) -> str:
    """
    发布小红书内容

    Args:
        title: 标题（必填，不超过40个字符）
        content: 正文内容（必填）
        image_paths: 图片路径列表（必填，支持jpg/jpeg/png/gif/webp格式）
        headless: 是否使用无头模式，默认False（建议使用有界面模式观察发布过程）
        chrome_path: Chrome浏览器可执行文件路径，可选

    Returns:
        发布结果消息
    """
    try:
        # 参数验证
        if not title.strip():
            return "❌ 标题不能为空"

        if len(title) > 40:
            return "❌ 标题长度不能超过40个字符"

        if not content.strip():
            return "❌ 正文内容不能为空"

        if not image_paths:
            return "❌ 必须提供至少一个图片"

        logger.info("开始发布小红书内容...")
        logger.info(f"标题: {title}")
        logger.info(f"内容: {content[:50]}..." if len(content) > 50 else f"内容: {content}")
        logger.info(f"图片: {image_paths}")

        # 创建浏览器管理器
        browser_manager = BrowserManager(
            headless=headless,
            chrome_path=chrome_path
        )

        async with browser_manager.get_page() as page:
            # 检查登录状态
            login_handler = XiaohongshuLogin(page)
            is_logged_in = await login_handler.check_login_status()

            if not is_logged_in:
                return "❌ 未登录，请先执行登录操作"

            # 创建发布处理器
            publish_handler = XiaohongshuPublish(page)

            # 执行发布
            success = await publish_handler.publish_content(
                title=title,
                content=content,
                image_paths=image_paths
            )

            if success:
                logger.success("🎉 发布成功！")
                return "🎉 小红书内容发布成功！"
            else:
                logger.error("❌ 发布失败")
                return "❌ 小红书内容发布失败"

    except Exception as e:
        error_msg = f"发布过程中发生错误: {e}"
        logger.error(error_msg)
        return f"❌ {error_msg}"


def main():
    """启动MCP服务器的主函数"""
    import sys

    # 配置日志 - 同时输出到控制台和文件
    logger.configure(
        handlers=[
            {
                "sink": sys.stderr,
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
                "level": "INFO"
            },
            {
                "sink": "logs/mcp_server.log",
                "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                "level": "INFO",
                "rotation": "10 MB"
            }
        ]
    )

    logger.info("🚀 启动小红书MCP服务器...")
    logger.info("📋 可用工具:")
    logger.info("   - xiaohongshu_login: 登录小红书账号")
    logger.info("   - xiaohongshu_check_status: 检查登录状态")
    logger.info("   - xiaohongshu_publish: 发布内容到小红书")
    logger.info("")
    logger.info("💡 使用方法:")
    logger.info("   1. 开发模式: uv run mcp dev src/xiaohongshu_mcp/server.py")
    logger.info("   2. 生产模式: uv run xiaohongshu-mcp-server")
    logger.info("")
    logger.info("🔗 当前模式: 标准MCP服务器")
    logger.info("📡 等待MCP客户端连接...")

    # 运行MCP服务器
    mcp.run()


if __name__ == "__main__":
    main()