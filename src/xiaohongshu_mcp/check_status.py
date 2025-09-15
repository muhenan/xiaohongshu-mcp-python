"""小红书登录状态检查工具"""

import argparse
import asyncio
import sys
from loguru import logger

from .browser.driver import BrowserManager
from .xiaohongshu.login import XiaohongshuLogin


async def main_async():
    """异步主函数"""
    parser = argparse.ArgumentParser(description="小红书登录状态检查工具")
    parser.add_argument(
        "--chrome-path",
        type=str,
        help="Chrome浏览器可执行文件路径"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细信息"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="使用无头模式（默认启用）"
    )

    args = parser.parse_args()

    # 配置日志
    log_level = "DEBUG" if args.verbose else "INFO"
    logger.configure(
        handlers=[
            {
                "sink": sys.stderr,
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                         "<level>{level: <8}</level> | "
                         "<level>{message}</level>",
                "level": log_level
            }
        ]
    )

    # 创建浏览器管理器（使用无头模式以提高速度）
    browser_manager = BrowserManager(
        headless=args.headless,
        chrome_path=args.chrome_path
    )

    try:
        async with browser_manager.get_page() as page:
            # 创建登录实例
            login_handler = XiaohongshuLogin(page)

            # 检查登录状态
            logger.info("正在检查小红书登录状态...")
            is_logged_in = await login_handler.check_login_status()

            # 显示结果
            if is_logged_in:
                logger.success("✅ 当前状态: 已登录")
                if args.verbose:
                    logger.info("Cookie文件位置: ~/.xiaohongshu_mcp/cookies.json")
                    logger.info("可以直接使用发布等功能")
                print("LOGGED_IN")  # 供脚本调用使用
                sys.exit(0)
            else:
                logger.warning("❌ 当前状态: 未登录")
                if args.verbose:
                    logger.info("需要先运行登录命令: uv run xiaohongshu-login")
                print("NOT_LOGGED_IN")  # 供脚本调用使用
                sys.exit(1)

    except KeyboardInterrupt:
        logger.info("用户取消检查")
        sys.exit(0)
    except Exception as e:
        logger.error(f"检查登录状态时发生错误: {e}")
        if args.verbose:
            import traceback
            logger.debug(f"详细错误信息:\n{traceback.format_exc()}")
        print("ERROR")  # 供脚本调用使用
        sys.exit(2)


def main():
    """同步主函数入口"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()