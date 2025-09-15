"""小红书发布模块"""

import asyncio
import os
from pathlib import Path
from typing import List
from loguru import logger
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError


class XiaohongshuPublish:
    """小红书发布操作类"""

    def __init__(self, page: Page):
        self.page = page
        self.publish_url = "https://creator.xiaohongshu.com/publish/publish?source=official"

    async def publish_content(self, title: str, content: str, image_paths: List[str]) -> bool:
        """
        发布图文内容

        Args:
            title: 标题
            content: 正文内容
            image_paths: 图片路径列表

        Returns:
            bool: 发布成功返回True，失败返回False
        """
        try:
            logger.info("开始发布内容...")

            # 验证图片文件
            if not self._validate_images(image_paths):
                return False

            # 导航到发布页面
            await self._navigate_to_publish_page()

            # 上传图片
            await self._upload_images(image_paths)

            # 填写标题和内容
            await self._fill_content(title, content)

            # 提交发布
            await self._submit_publish()

            logger.success("🎉 内容发布成功！")
            return True

        except Exception as e:
            logger.error(f"发布内容时出错: {e}")
            return False

    def _validate_images(self, image_paths: List[str]) -> bool:
        """验证图片文件"""
        if not image_paths:
            logger.error("图片列表不能为空")
            return False

        for path in image_paths:
            if not Path(path).exists():
                logger.error(f"图片文件不存在: {path}")
                return False

            if not Path(path).is_file():
                logger.error(f"路径不是文件: {path}")
                return False

        logger.info(f"验证通过，共 {len(image_paths)} 个图片文件")
        return True

    async def _navigate_to_publish_page(self) -> None:
        """导航到发布页面"""
        logger.info("导航到小红书发布页面...")

        # 设置更长的页面超时时间
        await self.page.goto(self.publish_url, timeout=60000)
        await self.page.wait_for_load_state("domcontentloaded")

        # 关键：必须等待 upload-content 元素可见
        logger.info("等待上传区域出现...")
        try:
            await self.page.wait_for_selector("div.upload-content", timeout=15000)
            logger.info("✅ upload-content 元素已出现")
        except PlaywrightTimeoutError:
            raise Exception("upload-content 元素等待超时，发布页面可能未正确加载")

        # 等待页面完全加载
        await asyncio.sleep(1)

        # 点击"上传图文"选项卡
        await self._click_upload_tab()

        # 再等待1秒确保页面稳定
        await asyncio.sleep(1)


    async def _click_upload_tab(self) -> None:
        """点击上传图文选项卡"""
        try:
            logger.info("查找上传图文选项卡...")

            # 方法1: 尝试直接通过更精确的选择器
            specific_selectors = [
                "[data-value='image']",  # 可能的data属性
                "[class*='image']",      # 包含image的class
                "div.creator-tab:nth-child(2)",  # 通常图文是第二个选项卡
            ]

            for selector in specific_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        await element.click()
                        logger.info(f"✅ 通过选择器 {selector} 成功点击选项卡")
                        await asyncio.sleep(1)
                        return
                except Exception:
                    continue

            # 方法2: 如果精确选择器失败，回退到文本匹配（优化版）
            tab_elements = await self.page.query_selector_all("div.creator-tab")
            logger.info(f"找到 {len(tab_elements)} 个选项卡元素")

            for i, element in enumerate(tab_elements):
                try:
                    logger.debug(f"检查选项卡 {i+1}...")

                    # 快速获取文本，设置短超时
                    text = await asyncio.wait_for(
                        element.text_content(),
                        timeout=1.0  # 1秒超时
                    )

                    if text and "上传图文" in text:
                        logger.info(f"✅ 找到并点击上传图文选项卡 (#{i+1})")
                        await element.click()
                        await asyncio.sleep(1)
                        return

                except asyncio.TimeoutError:
                    logger.debug(f"选项卡 {i+1} 超时，跳过")
                    continue
                except Exception as e:
                    logger.debug(f"选项卡 {i+1} 错误: {e}")
                    continue

            logger.info("未找到上传图文选项卡，可能已经在正确页面")

        except Exception as e:
            logger.warning(f"点击选项卡时出错: {e}，继续执行")

    async def _upload_images(self, image_paths: List[str]) -> None:
        """上传图片"""
        logger.info(f"开始上传 {len(image_paths)} 个图片...")

        try:
            # 等待上传输入框出现，缩短超时时间
            logger.info("等待上传输入框出现...")
            upload_input = await self.page.wait_for_selector(".upload-input", timeout=10000)
            logger.info("✅ 找到上传输入框")

            # 上传多个文件
            await upload_input.set_input_files(image_paths)
            logger.info(f"✅ 已设置 {len(image_paths)} 个文件进行上传")

            # 等待上传处理完成并转到编辑界面
            await self._wait_for_upload_complete()

        except PlaywrightTimeoutError:
            raise Exception("等待上传输入框超时，请检查页面是否正确加载")
        except Exception as e:
            raise Exception(f"上传图片失败: {e}")

    async def _wait_for_upload_complete(self) -> None:
        """等待图片上传完成并进入编辑界面"""
        logger.info("等待图片上传完成并进入编辑界面...")

        # 先等待基本的上传处理时间
        await asyncio.sleep(3)

        # 等待编辑界面的关键元素出现，这些是标题和内容输入框可能出现的时机
        edit_indicators = [
            "div.d-input input",  # 标题输入框
            ".d-input input",
            "input[placeholder*='标题']",
            "textarea",
            ".ql-editor",  # 富文本编辑器
            "[contenteditable='true']",  # 可编辑内容
            ".publish-form",
            ".edit-content"
        ]

        # 最多等待15秒，让页面从上传状态转到编辑状态
        for attempt in range(15):
            logger.info(f"检查编辑界面是否就绪... (尝试 {attempt + 1}/15)")

            for indicator in edit_indicators:
                try:
                    element = await self.page.query_selector(indicator)
                    if element:
                        logger.info(f"✅ 检测到编辑界面元素: {indicator}")
                        logger.info("✅ 图片上传完成，编辑界面已就绪")
                        return
                except:
                    continue

            # 检查是否还在上传状态（只有file input的情况）
            inputs = await self.page.query_selector_all("input")
            file_inputs_only = all(
                await input_elem.get_attribute("type") == "file"
                for input_elem in inputs
                if await input_elem.get_attribute("type")
            )

            if not file_inputs_only:
                logger.info("✅ 页面已离开纯上传状态")
                break

            await asyncio.sleep(1)

        logger.info("✅ 等待上传完成阶段结束，继续执行...")

    async def _fill_content(self, title: str, content: str) -> None:
        """填写标题和内容"""
        logger.info("填写标题和内容...")

        try:
            # 填写标题
            await self._fill_title(title)

            # 填写内容
            await self._fill_description(content)

        except Exception as e:
            raise Exception(f"填写内容失败: {e}")

    async def _fill_title(self, title: str) -> None:
        """填写标题"""
        try:
            # 先输出当前页面信息用于调试
            current_url = self.page.url
            page_title = await self.page.title()
            logger.info(f"当前页面URL: {current_url}")
            logger.info(f"当前页面标题: {page_title}")

            # 尝试多种标题输入框选择器
            title_selectors = [
                "div.d-input input",  # 标题输入框主选择器
                ".d-input input",
                "input[placeholder*='标题']",
                "input[placeholder*='title']",
                ".title-input",
                "[class*='title'] input",
                "textarea[placeholder*='标题']",
                "input[type='text']"
            ]

            title_input = None
            for i, selector in enumerate(title_selectors):
                try:
                    logger.info(f"尝试标题选择器 {i+1}/{len(title_selectors)}: {selector}")
                    title_input = await self.page.wait_for_selector(selector, timeout=3000)
                    if title_input:
                        logger.info(f"✅ 找到标题输入框: {selector}")
                        break
                except PlaywrightTimeoutError:
                    logger.debug(f"选择器 {selector} 未找到")
                    continue

            if not title_input:
                # 输出页面的所有input元素用于调试
                logger.warning("未找到标题输入框，查找页面中的所有input元素...")
                inputs = await self.page.query_selector_all("input")
                logger.info(f"页面中共有 {len(inputs)} 个input元素")

                for i, input_elem in enumerate(inputs):
                    try:
                        placeholder = await input_elem.get_attribute("placeholder")
                        class_name = await input_elem.get_attribute("class")
                        input_type = await input_elem.get_attribute("type")
                        logger.info(f"Input {i+1}: type={input_type}, placeholder='{placeholder}', class='{class_name}'")
                    except:
                        pass

                raise Exception("所有标题选择器都未找到")

            # 填写标题内容
            await title_input.fill(title)
            logger.info(f"✅ 标题填写完成: {title}")

            # 等待输入完成
            await asyncio.sleep(1)

        except Exception as e:
            raise Exception(f"填写标题失败: {e}")

    async def _fill_description(self, content: str) -> None:
        """填写正文描述"""
        try:
            # 尝试多种方式查找内容输入框
            content_element = await self._find_content_element()

            if content_element:
                # 填写正文内容
                await content_element.fill(content)
                logger.info("✅ 正文内容填写完成")
                await asyncio.sleep(1)
            else:
                raise Exception("未找到内容输入框")

        except Exception as e:
            raise Exception(f"填写正文失败: {e}")

    async def _find_content_element(self):
        """查找内容输入框，尝试多种方式"""
        try:
            # 方式1: 查找ql-editor
            try:
                element = await self.page.wait_for_selector("div.ql-editor", timeout=3000)
                if element:
                    logger.debug("使用ql-editor方式找到内容输入框")
                    return element
            except:
                pass

            # 方式2: 查找带placeholder的textbox
            try:
                element = await self._find_textbox_by_placeholder()
                if element:
                    logger.debug("使用placeholder方式找到内容输入框")
                    return element
            except:
                pass

            # 方式3: 通用textarea查找
            try:
                element = await self.page.wait_for_selector("textarea", timeout=3000)
                if element:
                    logger.debug("使用textarea方式找到内容输入框")
                    return element
            except:
                pass

            logger.error("所有方式都未找到内容输入框")
            return None

        except Exception as e:
            logger.error(f"查找内容输入框时出错: {e}")
            return None

    async def _find_textbox_by_placeholder(self):
        """通过placeholder查找textbox"""
        try:
            # 查找所有p元素
            p_elements = await self.page.query_selector_all("p")

            for element in p_elements:
                placeholder = await element.get_attribute("data-placeholder")
                if placeholder and "输入正文描述" in placeholder:
                    # 向上查找textbox父元素
                    current = element
                    for _ in range(5):
                        parent = await current.query_selector("xpath=..")
                        if not parent:
                            break

                        role = await parent.get_attribute("role")
                        if role == "textbox":
                            return parent

                        current = parent

            return None

        except Exception:
            return None

    async def _submit_publish(self) -> None:
        """提交发布"""
        logger.info("提交发布...")

        try:
            # 等待页面稳定
            await asyncio.sleep(1)

            # 查找提交按钮
            logger.info("等待提交按钮...")
            submit_button = await self.page.wait_for_selector(
                "div.submit div.d-button-content",
                timeout=10000
            )
            logger.info("✅ 找到提交按钮")

            await submit_button.click()
            logger.info("✅ 已点击发布按钮")

            # 等待发布请求处理
            await asyncio.sleep(3)
            logger.info("✅ 发布请求已提交")

        except PlaywrightTimeoutError:
            raise Exception("等待提交按钮超时")
        except Exception as e:
            raise Exception(f"提交发布失败: {e}")