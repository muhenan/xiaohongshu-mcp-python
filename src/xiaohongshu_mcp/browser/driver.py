"""浏览器驱动模块"""

from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from loguru import logger

from .cookies import CookieManager


class BrowserManager:
    """浏览器管理器"""

    def __init__(self, headless: bool = False, chrome_path: Optional[str] = None):
        self.headless = headless
        self.chrome_path = chrome_path
        self.cookie_manager = CookieManager()

    @asynccontextmanager
    async def get_page(self) -> AsyncGenerator[Page, None]:
        """获取浏览器页面的上下文管理器"""
        async with async_playwright() as playwright:
            # 启动浏览器
            launch_options = {
                "headless": self.headless,
                "args": [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ]
            }

            if self.chrome_path:
                launch_options["executable_path"] = self.chrome_path

            browser = await playwright.chromium.launch(**launch_options)

            try:
                # 创建浏览器上下文
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36"
                )

                # 加载cookies
                cookies = self.cookie_manager.load_cookies()
                if cookies:
                    await context.add_cookies(cookies)
                    logger.info(f"已加载 {len(cookies)} 个cookies")

                # 创建页面
                page = await context.new_page()

                try:
                    yield page
                finally:
                    # 保存cookies
                    current_cookies = await context.cookies()
                    if current_cookies:
                        self.cookie_manager.save_cookies(current_cookies)

                    await page.close()
                    await context.close()
            finally:
                await browser.close()

    async def save_current_cookies(self, page: Page) -> None:
        """手动保存当前页面的cookies"""
        context = page.context
        cookies = await context.cookies()
        if cookies:
            self.cookie_manager.save_cookies(cookies)
            logger.info(f"手动保存了 {len(cookies)} 个cookies")