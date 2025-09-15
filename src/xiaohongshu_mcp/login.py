"""小红书登录命令行工具"""

import argparse
import asyncio
import sys
from loguru import logger

from .browser.driver import BrowserManager
from .xiaohongshu.login import XiaohongshuLogin


async def main_async():
    """异步主函数"""
    parser = argparse.ArgumentParser(description="小红书登录工具")
    parser.add_argument(
        "--chrome-path",
        type=str,
        help="Chrome浏览器可执行文件路径"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="使用无头模式（登录时建议关闭此选项）"
    )

    args = parser.parse_args()

    # 配置日志
    logger.configure(
        handlers=[
            {
                "sink": sys.stderr,
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                         "<level>{level: <8}</level> | "
                         "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                         "<level>{message}</level>",
                "level": "INFO"
            }
        ]
    )

    # 登录时强制使用有界面模式，便于用户扫码
    headless = False if not args.headless else args.headless
    if headless:
        logger.warning("登录过程建议使用有界面模式，将自动切换到有界面模式")
        headless = False

    # 创建浏览器管理器
    browser_manager = BrowserManager(
        headless=headless,
        chrome_path=args.chrome_path
    )

    try:
        async with browser_manager.get_page() as page:
            # 创建登录实例
            login_handler = XiaohongshuLogin(page)

            # 检查当前登录状态
            is_logged_in = await login_handler.check_login_status()
            logger.info(f"当前登录状态: {'已登录' if is_logged_in else '未登录'}")

            if is_logged_in:
                logger.success("✅ 已经处于登录状态，无需重新登录")
                return

            # 开始登录流程
            logger.info("开始登录流程...")
            success = await login_handler.login()

            if success:
                # 再次确认登录状态
                final_status = await login_handler.check_login_status()
                if final_status:
                    # 手动保存cookies
                    await browser_manager.save_current_cookies(page)
                    logger.success("✅ 登录成功！Cookies已保存，浏览器即将关闭...")

                    # 等待2秒让用户看到成功信息，然后自动关闭
                    await asyncio.sleep(2)
                else:
                    logger.error("❌ 登录流程完成但仍未检测到登录状态")
                    sys.exit(1)
            else:
                logger.error("❌ 登录失败")
                sys.exit(1)

    except KeyboardInterrupt:
        logger.info("用户取消登录")
        sys.exit(0)
    except Exception as e:
        logger.error(f"登录过程中发生错误: {e}")
        sys.exit(1)


def main():
    """同步主函数入口"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()