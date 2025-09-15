"""小红书登录模块"""

import asyncio
from loguru import logger
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError


class XiaohongshuLogin:
    """小红书登录操作类"""

    def __init__(self, page: Page):
        self.page = page
        self.base_url = "https://www.xiaohongshu.com/explore"
        # 登录状态检测元素
        self.login_indicator = ".main-container .user .link-wrapper .channel"

    async def check_login_status(self) -> bool:
        """
        检查登录状态

        Returns:
            bool: True表示已登录，False表示未登录
        """
        try:
            logger.info("正在检查登录状态...")

            # 导航到小红书探索页，使用更短的超时时间
            await self.page.goto(self.base_url, timeout=15000)

            # 只等待domcontentloaded，不等待networkidle
            await self.page.wait_for_load_state("domcontentloaded")

            # 等待页面基本元素加载
            await asyncio.sleep(2)

            # 尝试多种方式检查登录状态
            return await self._check_login_with_multiple_methods()

        except Exception as e:
            logger.error(f"检查登录状态时出错: {e}")
            return False

    async def _check_login_with_multiple_methods(self) -> bool:
        """使用多种方法检查登录状态"""

        # 方法1: 检查原始登录指示器
        try:
            login_element = await self.page.query_selector(self.login_indicator)
            if login_element:
                logger.info("✅ 通过主要指示器检测到已登录状态")
                return True
        except Exception as e:
            logger.debug(f"主要指示器检查失败: {e}")

        # 方法2: 检查是否有用户头像或用户相关元素
        user_indicators = [
            ".user-avatar",
            "[class*='user']",
            "[class*='avatar']",
            ".header-user",
            "[data-testid*='user']"
        ]

        for indicator in user_indicators:
            try:
                element = await self.page.query_selector(indicator)
                if element:
                    logger.info(f"✅ 通过用户指示器 {indicator} 检测到已登录状态")
                    return True
            except Exception:
                continue

        # 方法3: 检查页面内容是否包含登录相关文本
        try:
            content = await self.page.content()
            if any(keyword in content for keyword in ["个人主页", "我的", "设置", "退出登录", "发布", "创作中心"]):
                logger.info("✅ 通过页面内容检测到已登录状态")
                return True
        except Exception as e:
            logger.debug(f"页面内容检查失败: {e}")

        # 方法4: 检查URL是否重定向到登录页
        try:
            current_url = self.page.url
            if "login" in current_url.lower() or "signin" in current_url.lower():
                logger.info("❌ 页面重定向到登录页，确认未登录")
                return False
        except Exception:
            pass

        logger.info("❌ 所有方法都未检测到登录状态")
        return False

    async def login(self) -> bool:
        """
        执行登录流程

        Returns:
            bool: 登录成功返回True，失败返回False
        """
        try:
            logger.info("开始登录流程...")

            # 导航到小红书探索页，这会触发登录弹窗
            await self.page.goto(self.base_url)
            await self.page.wait_for_load_state("networkidle")

            # 等待2秒让页面完全加载
            await asyncio.sleep(2)

            # 检查是否已经登录
            if await self.check_login_status():
                logger.info("已经处于登录状态，无需重新登录")
                return True

            logger.info("等待用户扫码登录...")
            logger.info("请在浏览器中扫描二维码完成登录")

            # 等待登录成功的元素出现，最多等待5分钟
            try:
                await self.page.wait_for_selector(
                    self.login_indicator,
                    timeout=300000  # 5分钟超时
                )
                logger.success("🎉 检测到登录成功！正在保存登录状态...")
                return True

            except PlaywrightTimeoutError:
                logger.error("❌ 登录超时，请检查是否完成扫码")
                return False

        except Exception as e:
            logger.error(f"登录过程中出错: {e}")
            return False

    async def logout(self) -> bool:
        """
        执行登出操作（可选实现）

        Returns:
            bool: 登出成功返回True，失败返回False
        """
        try:
            logger.info("开始登出流程...")
            # 这里可以实现具体的登出逻辑
            # 目前简单返回True
            return True
        except Exception as e:
            logger.error(f"登出时出错: {e}")
            return False