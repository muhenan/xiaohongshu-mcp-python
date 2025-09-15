"""Cookie管理模块"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger


class CookieManager:
    """Cookie管理器，负责保存和加载浏览器Cookies"""

    def __init__(self, cookie_file: str = None):
        if cookie_file is None:
            # 默认存储在临时目录
            self.cookie_file = Path.home() / ".xiaohongshu_mcp" / "cookies.json"
        else:
            self.cookie_file = Path(cookie_file)

        # 确保目录存在
        self.cookie_file.parent.mkdir(parents=True, exist_ok=True)

    def save_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        """保存cookies到文件"""
        try:
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            logger.info(f"Cookies已保存到: {self.cookie_file}")
        except Exception as e:
            logger.error(f"保存cookies失败: {e}")
            raise

    def load_cookies(self) -> List[Dict[str, Any]]:
        """从文件加载cookies"""
        try:
            if not self.cookie_file.exists():
                logger.warning(f"Cookie文件不存在: {self.cookie_file}")
                return []

            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)

            logger.info(f"成功加载 {len(cookies)} 个cookies")
            return cookies
        except Exception as e:
            logger.error(f"加载cookies失败: {e}")
            return []

    def clear_cookies(self) -> None:
        """清除保存的cookies"""
        try:
            if self.cookie_file.exists():
                self.cookie_file.unlink()
                logger.info("Cookies已清除")
        except Exception as e:
            logger.error(f"清除cookies失败: {e}")