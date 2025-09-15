"""小红书发布命令行工具"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import List
from loguru import logger

from .browser.driver import BrowserManager
from .xiaohongshu.login import XiaohongshuLogin
from .xiaohongshu.publish import XiaohongshuPublish


async def main_async():
    """异步主函数"""
    parser = argparse.ArgumentParser(description="小红书内容发布工具")
    parser.add_argument(
        "--title", "-t",
        type=str,
        required=True,
        help="标题（必填）"
    )
    parser.add_argument(
        "--content", "-c",
        type=str,
        required=True,
        help="正文内容（必填）"
    )
    parser.add_argument(
        "--images", "-i",
        type=str,
        nargs="+",
        required=True,
        help="图片路径列表（必填，支持多个）"
    )
    parser.add_argument(
        "--chrome-path",
        type=str,
        help="Chrome浏览器可执行文件路径"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="使用无头模式（发布时建议关闭此选项）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预检模式，只验证参数不实际发布"
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

    # 验证参数
    if not validate_args(args):
        sys.exit(1)

    if args.dry_run:
        logger.info("✅ 参数验证通过（预检模式）")
        return

    # 发布时建议使用有界面模式
    headless = args.headless
    if not headless:
        logger.info("使用有界面模式，便于观察发布过程")

    # 创建浏览器管理器
    browser_manager = BrowserManager(
        headless=headless,
        chrome_path=args.chrome_path
    )

    try:
        async with browser_manager.get_page() as page:
            # 检查登录状态
            login_handler = XiaohongshuLogin(page)
            is_logged_in = await login_handler.check_login_status()

            if not is_logged_in:
                logger.error("❌ 未登录，请先运行: uv run xiaohongshu-login")
                sys.exit(1)

            logger.success("✅ 登录状态正常")

            # 创建发布实例
            publish_handler = XiaohongshuPublish(page)

            # 执行发布
            logger.info(f"开始发布内容...")
            logger.info(f"标题: {args.title}")
            logger.info(f"内容: {args.content[:50]}..." if len(args.content) > 50 else f"内容: {args.content}")
            logger.info(f"图片: {args.images}")

            success = await publish_handler.publish_content(
                title=args.title,
                content=args.content,
                image_paths=args.images
            )

            if success:
                logger.success("🎉 发布成功！")
            else:
                logger.error("❌ 发布失败")
                sys.exit(1)

    except KeyboardInterrupt:
        logger.info("用户取消发布")
        sys.exit(0)
    except Exception as e:
        logger.error(f"发布过程中发生错误: {e}")
        sys.exit(1)


def validate_args(args) -> bool:
    """验证命令行参数"""
    logger.info("验证发布参数...")

    # 验证标题
    if not args.title.strip():
        logger.error("标题不能为空")
        return False

    if len(args.title) > 40:
        logger.error("标题长度不能超过40个字符")
        return False

    # 验证内容
    if not args.content.strip():
        logger.error("正文内容不能为空")
        return False

    # 验证图片
    if not args.images:
        logger.error("必须提供至少一个图片")
        return False

    for image_path in args.images:
        path = Path(image_path)
        if not path.exists():
            logger.error(f"图片文件不存在: {image_path}")
            return False

        if not path.is_file():
            logger.error(f"路径不是文件: {image_path}")
            return False

        # 检查文件扩展名
        if path.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            logger.error(f"不支持的图片格式: {image_path}")
            return False

    logger.info("✅ 参数验证通过")
    return True


def main():
    """同步主函数入口"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()