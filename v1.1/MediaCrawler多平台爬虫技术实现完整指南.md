# MediaCrawler 多平台爬虫技术实现完整指南

> 本文档详细记录MediaCrawler项目的技术实现，可直接照此实现各平台爬虫功能。

---

## 一、项目概述

### 1.1 项目定位

MediaCrawler是一个基于Playwright的多平台自媒体数据采集工具，核心特点是**无需逆向加密算法**，通过浏览器自动化获取签名参数。

### 1.2 支持平台

| 平台 | 代码 | 关键词搜索 | 帖子详情 | 评论爬取 | 二级评论 | 创作者主页 |
|------|------|-----------|---------|---------|---------|-----------|
| 小红书 | xhs | ✅ | ✅ | ✅ | ✅ | ✅ |
| 抖音 | dy | ✅ | ✅ | ✅ | ✅ | ✅ |
| 快手 | ks | ✅ | ✅ | ✅ | ✅ | ✅ |
| B站 | bili | ✅ | ✅ | ✅ | ✅ | ✅ |
| 微博 | wb | ✅ | ✅ | ✅ | ✅ | ✅ |
| 贴吧 | tieba | ✅ | ✅ | ✅ | ✅ | ✅ |
| 知乎 | zhihu | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 二、核心技术原理

### 2.1 为什么无需逆向？

**传统爬虫困境：**
```
请求 → 需要签名参数(x-s, x-t等) → 逆向JS加密算法 → 难度极高
```

**MediaCrawler方案：**
```
Playwright浏览器 → 保留登录态 → 执行平台内置JS → 直接获取签名
```

**关键洞察：** 小红书等平台的签名函数是前端内置的，在浏览器环境中可以直接调用。只要在已登录的浏览器上下文中执行JS，就能获取正确的签名参数。

### 2.2 技术架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MediaCrawler 架构                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   main.py (入口)                                                    │
│       │                                                             │
│       ▼                                                             │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    base/                                     │  │
│   │  ├── base_crawler.py    # 爬虫基类                           │  │
│   │  └── base_login.py      # 登录基类                           │  │
│   └─────────────────────────────────────────────────────────────┘  │
│       │                                                             │
│       ▼                                                             │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                 media_platform/xhs/                          │  │
│   │  ├── core.py            # 爬虫核心逻辑                        │  │
│   │  ├── client.py          # API客户端封装                       │  │
│   │  ├── login.py           # 登录处理                            │  │
│   │  ├── field.py           # 数据模型定义                        │  │
│   │  ├── playwright_sign.py # Playwright签名获取                  │  │
│   │  └── xhs_sign.py        # 小红书签名处理                      │  │
│   └─────────────────────────────────────────────────────────────┘  │
│       │                                                             │
│       ▼                                                             │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    store/                                    │  │
│   │  ├── csv_store.py       # CSV存储                            │  │
│   │  ├── json_store.py      # JSON存储                           │  │
│   │  └── mysql_store.py     # MySQL存储                          │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 三、环境搭建

### 3.1 前置依赖

| 依赖 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.9+ | 推荐使用uv管理 |
| Node.js | 16.0.0+ | 抖音、知乎需要 |
| Playwright | 最新版 | 浏览器自动化 |

### 3.2 安装步骤

```bash
# 方式一：使用uv（推荐）
# 1. 安装uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 克隆项目
git clone https://github.com/NanmiCoder/MediaCrawler.git
cd MediaCrawler

# 3. 同步环境
uv sync

# 4. 安装浏览器驱动
uv run playwright install

# 方式二：使用原生Python
# 1. 创建虚拟环境
python -m venv venv

# Windows激活
venv\Scripts\activate

# Linux/Mac激活
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装浏览器驱动
playwright install
```

### 3.3 目录结构

```
MediaCrawler/
├── main.py                     # 入口文件
├── config/
│   └── base_config.py          # 核心配置文件
├── media_platform/
│   ├── xhs/                    # 小红书爬虫
│   │   ├── __init__.py
│   │   ├── core.py             # 爬虫核心
│   │   ├── client.py           # API客户端
│   │   ├── login.py            # 登录模块
│   │   ├── field.py            # 数据模型
│   │   ├── playwright_sign.py  # 签名获取
│   │   ├── xhs_sign.py         # 签名处理
│   │   ├── exception.py        # 异常定义
│   │   ├── extractor.py        # 数据提取
│   │   └── help.py             # 辅助函数
│   ├── douyin/                 # 抖音爬虫
│   ├── kuaishou/               # 快手爬虫
│   ├── bilibili/               # B站爬虫
│   ├── weibo/                  # 微博爬虫
│   ├── tieba/                  # 贴吧爬虫
│   └── zhihu/                  # 知乎爬虫
├── base/
│   ├── base_crawler.py         # 爬虫基类
│   └── base_login.py           # 登录基类
├── store/
│   ├── csv_store.py            # CSV存储
│   ├── json_store.py           # JSON存储
│   └── mysql_store.py          # MySQL存储
├── proxy/
│   └── proxy_ip_pool.py        # 代理池
├── cache/
│   └── cache.py                # 缓存系统
├── tools/
│   └── utils.py                # 工具函数
├── model/
│   └── models.py               # 数据库模型
├── browser_data/               # 登录态缓存目录
└── data/                       # 数据输出目录
```

---

## 四、核心配置详解

### 4.1 配置文件 (config/base_config.py)

```python
# -*- coding: utf-8 -*-
"""
MediaCrawler 核心配置文件
所有可配置项及说明
"""

# ==================== 平台配置 ====================

# 目标平台: xhs(小红书) / dy(抖音) / ks(快手) / bili(B站) / wb(微博) / tieba(贴吧) / zhihu(知乎)
PLATFORM = "xhs"

# 登录方式: qrcode(二维码) / phone(手机号) / cookie(Cookie)
LOGIN_TYPE = "qrcode"

# 爬取类型: search(关键词搜索) / detail(指定帖子) / creator(创作者主页)
CRAWLER_TYPE = "search"


# ==================== 搜索配置 ====================

# 搜索关键词列表（搜索模式必填）
KEYWORDS = [
    "游戏",
    "原神",
    "王者荣耀",
]

# 指定帖子ID列表（详情模式必填）
# 小红书帖子ID获取方式：从帖子URL中提取
# 例如：https://www.xiaohongshu.com/explore/xxxxxx 中的 xxxxxx
NOTE_IDS = [
    "note_id_1",
    "note_id_2",
]

# 指定创作者ID列表（创作者模式必填）
CREATOR_IDS = [
    "creator_id_1",
]


# ==================== 爬取控制 ====================

# 是否开启评论爬取
ENABLE_GET_COMMENTS = True

# 是否开启二级评论爬取
ENABLE_GET_SUB_COMMENTS = True

# 最大爬取笔记数量
CRAWLER_MAX_NOTES = 50

# 最大爬取评论数量（每篇笔记）
CRAWLER_MAX_COMMENTS = 100


# ==================== 浏览器配置 ====================

# 是否开启无头模式
# 注意：登录时必须设为False，否则无法显示二维码
HEADLESS = False

# 浏览器数据保存路径
BROWSER_DATA_DIR = "browser_data"


# ==================== 代理配置 ====================

# 是否启用IP代理
ENABLE_IP_PROXY = False

# 代理池配置（需自行搭建代理池）
IP_PROXY_POOL_API = ""


# ==================== 数据存储配置 ====================

# 存储方式: csv / json / mysql / sqlite
SAVE_DATA_OPTION = "csv"

# MySQL配置（选择mysql存储时需要）
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "password"
MYSQL_DATABASE = "media_crawler"


# ==================== 请求控制 ====================

# 请求间隔时间（秒），避免请求过快被封
CRAWLER_REQUEST_INTERVAL = 1.0

# 最大重试次数
MAX_RETRY = 3

# 请求超时时间（秒）
REQUEST_TIMEOUT = 30
```

---

## 五、小红书爬虫完整实现

### 5.1 登录模块 (login.py)

```python
# -*- coding: utf-8 -*-
"""
小红书登录模块
支持二维码扫码登录，登录态持久化
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page, Playwright
from playwright.async_api import async_playwright


class XHSLogin:
    """
    小红书登录处理类
    
    核心功能：
    1. 二维码扫码登录
    2. 登录态持久化存储
    3. 登录态检测与恢复
    
    Attributes:
        browser_data_dir: 浏览器数据存储目录
        headless: 是否无头模式
        timeout: 登录超时时间（秒）
    """
    
    def __init__(
        self,
        browser_data_dir: str = "browser_data/xhs",
        headless: bool = False,
        timeout: int = 120
    ):
        """
        初始化登录处理器
        
        Args:
            browser_data_dir: 浏览器数据目录
            headless: 是否无头模式（登录时必须为False）
            timeout: 登录超时时间
        """
        self.browser_data_dir = Path(browser_data_dir)
        self.headless = headless
        self.timeout = timeout
        self.state_file = self.browser_data_dir / "state.json"
        
        # 确保目录存在
        self.browser_data_dir.mkdir(parents=True, exist_ok=True)
    
    async def login(self) -> BrowserContext:
        """
        执行登录流程
        
        Returns:
            已登录的浏览器上下文
        
        流程：
        1. 检查是否存在已保存的登录态
        2. 如果存在，尝试加载并验证
        3. 如果不存在或验证失败，执行扫码登录
        4. 保存登录态
        """
        async with async_playwright() as playwright:
            # 启动浏览器
            browser = await self._launch_browser(playwright)
            
            # 尝试加载已保存的登录态
            if self.state_file.exists():
                context = await self._load_saved_state(browser)
                if await self._check_login_status(context):
                    print("✅ 使用已保存的登录态")
                    return context
                else:
                    print("⚠️ 登录态已过期，需要重新登录")
            
            # 执行扫码登录
            context = await self._qrcode_login(browser)
            return context
    
    async def _launch_browser(self, playwright: Playwright) -> Browser:
        """
        启动浏览器
        
        Args:
            playwright: Playwright实例
        
        Returns:
            浏览器实例
        """
        return await playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",  # 隐藏自动化特征
            ]
        )
    
    async def _load_saved_state(self, browser: Browser) -> BrowserContext:
        """
        加载已保存的登录态
        
        Args:
            browser: 浏览器实例
        
        Returns:
            浏览器上下文
        """
        return await browser.new_context(
            storage_state=str(self.state_file),
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    
    async def _check_login_status(self, context: BrowserContext) -> bool:
        """
        检查登录状态
        
        Args:
            context: 浏览器上下文
        
        Returns:
            是否已登录
        """
        page = await context.new_page()
        try:
            await page.goto("https://www.xiaohongshu.com")
            await page.wait_for_load_state("networkidle")
            
            # 检查是否存在登录按钮（未登录状态）
            login_btn = await page.query_selector('.login-btn')
            return login_btn is None
        except Exception:
            return False
        finally:
            await page.close()
    
    async def _qrcode_login(self, browser: Browser) -> BrowserContext:
        """
        二维码扫码登录
        
        Args:
            browser: 浏览器实例
        
        Returns:
            已登录的浏览器上下文
        
        流程：
        1. 打开小红书首页
        2. 点击登录按钮
        3. 等待用户扫码
        4. 检测登录成功
        5. 保存登录态
        """
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # 访问小红书首页
            await page.goto("https://www.xiaohongshu.com")
            await page.wait_for_load_state("networkidle")
            
            print("📱 请使用小红书APP扫描二维码登录...")
            
            # 点击登录按钮
            login_btn = await page.query_selector('.login-btn')
            if login_btn:
                await login_btn.click()
            
            # 等待登录成功（检测登录按钮消失）
            await page.wait_for_selector('.login-btn', state="hidden", timeout=self.timeout * 1000)
            
            print("✅ 登录成功！")
            
            # 保存登录态
            await context.storage_state(path=str(self.state_file))
            print("💾 登录态已保存")
            
            return context
            
        except Exception as e:
            await context.close()
            raise Exception(f"登录失败: {e}")


# 使用示例
async def main():
    login = XHSLogin(headless=False)
    context = await login.login()
    print("登录完成，可以开始爬取")


if __name__ == "__main__":
    asyncio.run(main())
```

### 5.2 签名获取模块 (playwright_sign.py)

```python
# -*- coding: utf-8 -*-
"""
小红书签名获取模块
通过Playwright浏览器环境获取签名参数
"""

import json
from typing import Dict, Optional
from playwright.async_api import Page


class PlaywrightSign:
    """
    通过Playwright获取小红书签名参数
    
    核心原理：
    小红书前端内置了签名函数 window._webmsxyw
    在浏览器环境中可以直接调用，无需逆向
    
    Attributes:
        page: Playwright页面对象
    """
    
    def __init__(self, page: Page):
        """
        初始化签名获取器
        
        Args:
            page: Playwright页面对象
        """
        self.page = page
    
    async def get_sign(self, url: str, data: Optional[dict] = None) -> Dict[str, str]:
        """
        获取请求签名参数
        
        Args:
            url: 请求URL
            data: 请求数据（POST请求时需要）
        
        Returns:
            签名参数字典，包含：
            - x-s: 签名字符串
            - x-t: 时间戳签名
            - x-s-common: 通用签名
        
        实现原理：
        1. 在浏览器上下文中执行JS代码
        2. 调用小红书内置的签名函数
        3. 返回签名结果
        """
        # 构建JS代码
        js_code = f"""
        () => {{
            const url = "{url}";
            const data = {json.dumps(data) if data else 'null'};
            
            // 调用小红书内置签名函数
            // window._webmsxyw 是小红书前端的签名函数
            const signResult = window._webmsxyw(url, data);
            
            return {{
                'x-s': signResult['X-s'],
                'x-t': signResult['X-t'],
                'x-s-common': signResult['X-s-common']
            }};
        }}
        """
        
        # 在浏览器中执行JS
        result = await self.page.evaluate(js_code)
        return result
    
    async def get_search_sign(self, keyword: str, page_num: int = 1) -> Dict[str, str]:
        """
        获取搜索接口签名
        
        Args:
            keyword: 搜索关键词
            page_num: 页码
        
        Returns:
            签名参数
        """
        url = "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes"
        params = {
            "keyword": keyword,
            "page": page_num,
            "page_size": 20,
        }
        return await self.get_sign(url, params)
    
    async def get_comment_sign(self, note_id: str, cursor: str = "") -> Dict[str, str]:
        """
        获取评论接口签名
        
        Args:
            note_id: 笔记ID
            cursor: 分页游标
        
        Returns:
            签名参数
        """
        url = "https://edith.xiaohongshu.com/api/sns/web/v2/comment/page"
        params = {
            "note_id": note_id,
            "cursor": cursor,
        }
        return await self.get_sign(url, params)
```

### 5.3 API客户端模块 (client.py)

```python
# -*- coding: utf-8 -*-
"""
小红书API客户端
封装所有与小红书交互的HTTP请求
"""

import json
import uuid
from typing import Dict, List, Optional
from urllib.parse import urlencode

import aiohttp
from playwright.async_api import Page

from .playwright_sign import PlaywrightSign
from .exception import XHSApiException


class XHSClient:
    """
    小红书API客户端
    
    封装所有小红书API请求，包括：
    - 搜索笔记
    - 获取笔记详情
    - 获取评论
    - 获取创作者信息
    
    Attributes:
        page: Playwright页面对象
        sign_getter: 签名获取器
        cookies: Cookie字符串
        timeout: 请求超时时间
    """
    
    # API端点
    API_BASE = "https://edith.xiaohongshu.com"
    SEARCH_URL = f"{API_BASE}/api/sns/web/v1/search/notes"
    NOTE_DETAIL_URL = f"{API_BASE}/api/sns/web/v1/feed"
    COMMENT_URL = f"{API_BASE}/api/sns/web/v2/comment/page"
    SUB_COMMENT_URL = f"{API_BASE}/api/sns/web/v2/comment/sub/page"
    USER_INFO_URL = f"{API_BASE}/api/sns/web/v1/user/otherinfo"
    
    def __init__(
        self,
        page: Page,
        cookies: str,
        timeout: int = 30
    ):
        """
        初始化客户端
        
        Args:
            page: Playwright页面对象（用于获取签名）
            cookies: Cookie字符串
            timeout: 请求超时时间
        """
        self.page = page
        self.sign_getter = PlaywrightSign(page)
        self.cookies = cookies
        self.timeout = timeout
        
        # 请求头模板
        self.base_headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            "content-type": "application/json;charset=UTF-8",
            "origin": "https://www.xiaohongshu.com",
            "referer": "https://www.xiaohongshu.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
    
    async def search_notes(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        sort: str = "general"
    ) -> Dict:
        """
        搜索笔记
        
        Args:
            keyword: 搜索关键词
            page: 页码，从1开始
            page_size: 每页数量，默认20
            sort: 排序方式
                - general: 综合排序
                - time_descending: 最新发布
                - hot_descending: 最热
        
        Returns:
            搜索结果字典，包含：
            - data.items: 笔记列表
            - data.cursor: 下一页游标
        
        API文档：
            POST /api/sns/web/v1/search/notes
        """
        # 构建请求参数
        params = {
            "keyword": keyword,
            "page": page,
            "page_size": page_size,
            "search_id": str(uuid.uuid4()),  # 随机搜索ID
            "sort": sort,
            "type": "notes",  # 搜索类型：笔记
        }
        
        # 获取签名
        sign_params = await self.sign_getter.get_sign(self.SEARCH_URL, params)
        
        # 构建请求头
        headers = {
            **self.base_headers,
            "cookie": self.cookies,
            **sign_params,  # 添加签名参数
        }
        
        # 发送请求
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.SEARCH_URL,
                params=params,
                headers=headers,
                timeout=self.timeout
            ) as response:
                result = await response.json()
                
                if result.get("code") != 0:
                    raise XHSApiException(f"搜索失败: {result.get('msg')}")
                
                return result
    
    async def get_note_detail(self, note_id: str) -> Dict:
        """
        获取笔记详情
        
        Args:
            note_id: 笔记ID
        
        Returns:
            笔记详情字典
        
        API文档：
            POST /api/sns/web/v1/feed
        """
        params = {
            "source_note_id": note_id,
            "image_formats": ["jpg", "webp", "avif"],
            "extra": {"need_body_topic": 1}
        }
        
        sign_params = await self.sign_getter.get_sign(self.NOTE_DETAIL_URL, params)
        
        headers = {
            **self.base_headers,
            "cookie": self.cookies,
            **sign_params,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.NOTE_DETAIL_URL,
                json=params,
                headers=headers,
                timeout=self.timeout
            ) as response:
                result = await response.json()
                
                if result.get("code") != 0:
                    raise XHSApiException(f"获取详情失败: {result.get('msg')}")
                
                return result
    
    async def get_note_comments(
        self,
        note_id: str,
        cursor: str = "",
        top_comment_id: str = ""
    ) -> Dict:
        """
        获取笔记评论
        
        Args:
            note_id: 笔记ID
            cursor: 分页游标，首次请求为空
            top_comment_id: 置顶评论ID（可选）
        
        Returns:
            评论数据字典，包含：
            - data.comments: 评论列表
            - data.cursor: 下一页游标
            - data.has_more: 是否有更多
        
        API文档：
            GET /api/sns/web/v2/comment/page
        """
        params = {
            "note_id": note_id,
            "cursor": cursor,
            "top_comment_id": top_comment_id,
            "image_formats": "jpg,webp,avif",
        }
        
        sign_params = await self.sign_getter.get_sign(self.COMMENT_URL, params)
        
        headers = {
            **self.base_headers,
            "cookie": self.cookies,
            **sign_params,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.COMMENT_URL,
                params=params,
                headers=headers,
                timeout=self.timeout
            ) as response:
                result = await response.json()
                
                if result.get("code") != 0:
                    raise XHSApiException(f"获取评论失败: {result.get('msg')}")
                
                return result
    
    async def get_sub_comments(
        self,
        root_comment_id: str,
        num: int = 30,
        cursor: str = ""
    ) -> Dict:
        """
        获取二级评论（回复）
        
        Args:
            root_comment_id: 根评论ID
            num: 每页数量
            cursor: 分页游标
        
        Returns:
            二级评论数据
        
        API文档：
            GET /api/sns/web/v2/comment/sub/page
        """
        params = {
            "root_comment_id": root_comment_id,
            "num": num,
            "cursor": cursor,
        }
        
        sign_params = await self.sign_getter.get_sign(self.SUB_COMMENT_URL, params)
        
        headers = {
            **self.base_headers,
            "cookie": self.cookies,
            **sign_params,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.SUB_COMMENT_URL,
                params=params,
                headers=headers,
                timeout=self.timeout
            ) as response:
                result = await response.json()
                
                if result.get("code") != 0:
                    raise XHSApiException(f"获取二级评论失败: {result.get('msg')}")
                
                return result
    
    async def get_user_info(self, user_id: str) -> Dict:
        """
        获取用户信息
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户信息字典
        
        API文档：
            GET /api/sns/web/v1/user/otherinfo
        """
        params = {
            "target_user_id": user_id,
        }
        
        sign_params = await self.sign_getter.get_sign(self.USER_INFO_URL, params)
        
        headers = {
            **self.base_headers,
            "cookie": self.cookies,
            **sign_params,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.USER_INFO_URL,
                params=params,
                headers=headers,
                timeout=self.timeout
            ) as response:
                result = await response.json()
                
                if result.get("code") != 0:
                    raise XHSApiException(f"获取用户信息失败: {result.get('msg')}")
                
                return result
```

### 5.4 数据模型 (field.py)

```python
# -*- coding: utf-8 -*-
"""
小红书数据模型定义
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class XHSUser:
    """
    小红书用户数据模型
    
    Attributes:
        user_id: 用户ID
        nickname: 昵称
        avatar: 头像URL
        desc: 简介
        ip_location: IP属地
        follows: 关注数
        fans: 粉丝数
        interaction: 获赞与收藏数
    """
    user_id: str
    nickname: str
    avatar: str
    desc: str = ""
    ip_location: str = ""
    follows: int = 0
    fans: int = 0
    interaction: int = 0


@dataclass
class XHSComment:
    """
    小红书评论数据模型
    
    Attributes:
        comment_id: 评论ID
        content: 评论内容
        create_time: 创建时间
        ip_location: IP属地
        liked_count: 点赞数
        user: 评论用户
        sub_comments: 子评论列表
        pictures: 评论图片列表
    """
    comment_id: str
    content: str
    create_time: str
    ip_location: str = ""
    liked_count: int = 0
    user: Optional[XHSUser] = None
    sub_comments: List['XHSComment'] = field(default_factory=list)
    pictures: List[str] = field(default_factory=list)


@dataclass
class XHSNote:
    """
    小红书笔记数据模型
    
    Attributes:
        note_id: 笔记唯一ID
        title: 笔记标题
        desc: 笔记描述/正文
        note_type: 类型 (video/normal)
        video_url: 视频链接（视频笔记）
        images: 图片链接列表
        time: 发布时间
        last_update_time: 最后更新时间
        liked_count: 点赞数
        collected_count: 收藏数
        comment_count: 评论数
        share_count: 分享数
        user: 作者信息
        tags: 标签列表
        ip_location: IP属地
        at_user_list: @用户列表
        image_list: 图片详情列表
    """
    note_id: str
    title: str
    desc: str
    note_type: str  # "video" / "normal"
    video_url: Optional[str] = None
    images: List[str] = field(default_factory=list)
    time: str = ""
    last_update_time: str = ""
    liked_count: int = 0
    collected_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    user: Optional[XHSUser] = None
    tags: List[str] = field(default_factory=list)
    ip_location: str = ""
    at_user_list: List[XHSUser] = field(default_factory=list)
    image_list: List[dict] = field(default_factory=list)
    comments: List[XHSComment] = field(default_factory=list)


@dataclass
class XHSCreator:
    """
    小红书创作者数据模型
    
    Attributes:
        user_id: 用户ID
        nickname: 昵称
        avatar: 头像
        desc: 简介
        ip_location: IP属地
        follows: 关注数
        fans: 粉丝数
        interaction: 获赞与收藏数
        tag_list: 标签列表
    """
    user_id: str
    nickname: str
    avatar: str
    desc: str = ""
    ip_location: str = ""
    follows: int = 0
    fans: int = 0
    interaction: int = 0
    tag_list: List[str] = field(default_factory=list)
```

### 5.5 爬虫核心 (core.py)

```python
# -*- coding: utf-8 -*-
"""
小红书爬虫核心模块
实现完整的爬取流程
"""

import asyncio
import json
import time
from typing import Dict, List, Optional
from pathlib import Path

from playwright.async_api import BrowserContext, Page, async_playwright

from .client import XHSClient
from .field import XHSNote, XHSComment, XHSUser
from .login import XHSLogin
from .exception import XHSApiException


class XHSCrawler:
    """
    小红书爬虫核心类
    
    实现完整的爬取流程：
    1. 登录/加载登录态
    2. 搜索/获取笔记
    3. 获取笔记详情
    4. 爬取评论
    5. 存储数据
    
    Attributes:
        keywords: 搜索关键词列表
        note_ids: 指定笔记ID列表
        creator_ids: 创作者ID列表
        enable_comments: 是否爬取评论
        enable_sub_comments: 是否爬取二级评论
        max_notes: 最大爬取笔记数
        max_comments: 最大爬取评论数
        request_interval: 请求间隔（秒）
    """
    
    def __init__(
        self,
        keywords: List[str] = None,
        note_ids: List[str] = None,
        creator_ids: List[str] = None,
        enable_comments: bool = True,
        enable_sub_comments: bool = True,
        max_notes: int = 50,
        max_comments: int = 100,
        request_interval: float = 1.0,
        browser_data_dir: str = "browser_data/xhs",
        headless: bool = True,
    ):
        """
        初始化爬虫
        
        Args:
            keywords: 搜索关键词列表
            note_ids: 指定笔记ID列表
            creator_ids: 创作者ID列表
            enable_comments: 是否爬取评论
            enable_sub_comments: 是否爬取二级评论
            max_notes: 最大爬取笔记数
            max_comments: 最大爬取评论数
            request_interval: 请求间隔
            browser_data_dir: 浏览器数据目录
            headless: 是否无头模式
        """
        self.keywords = keywords or []
        self.note_ids = note_ids or []
        self.creator_ids = creator_ids or []
        self.enable_comments = enable_comments
        self.enable_sub_comments = enable_sub_comments
        self.max_notes = max_notes
        self.max_comments = max_comments
        self.request_interval = request_interval
        self.browser_data_dir = browser_data_dir
        self.headless = headless
        
        # 运行时变量
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.client: Optional[XHSClient] = None
        self.cookies: str = ""
        
        # 数据存储
        self.notes: List[XHSNote] = []
    
    async def start(self):
        """
        启动爬虫
        
        流程：
        1. 登录/加载登录态
        2. 初始化客户端
        3. 执行爬取任务
        4. 保存数据
        """
        print("🚀 启动小红书爬虫...")
        
        # 登录
        login = XHSLogin(
            browser_data_dir=self.browser_data_dir,
            headless=False,  # 登录时必须显示浏览器
        )
        self.context = await login.login()
        
        # 获取Page和Cookie
        self.page = await self.context.new_page()
        await self.page.goto("https://www.xiaohongshu.com")
        
        # 获取Cookie字符串
        cookies = await self.context.cookies()
        self.cookies = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        
        # 初始化客户端
        self.client = XHSClient(self.page, self.cookies)
        
        # 执行爬取
        if self.keywords:
            await self._crawl_by_search()
        elif self.note_ids:
            await self._crawl_by_note_ids()
        elif self.creator_ids:
            await self._crawl_by_creators()
        
        # 保存数据
        await self._save_data()
        
        print(f"✅ 爬取完成，共获取 {len(self.notes)} 篇笔记")
    
    async def _crawl_by_search(self):
        """
        通过关键词搜索爬取
        
        流程：
        1. 遍历关键词
        2. 搜索笔记
        3. 获取详情和评论
        """
        for keyword in self.keywords:
            print(f"🔍 搜索关键词: {keyword}")
            
            page_num = 1
            note_count = 0
            
            while note_count < self.max_notes:
                # 搜索笔记
                result = await self.client.search_notes(
                    keyword=keyword,
                    page=page_num
                )
                
                items = result.get("data", {}).get("items", [])
                if not items:
                    break
                
                for item in items:
                    if note_count >= self.max_notes:
                        break
                    
                    note_id = item.get("id") or item.get("note_id")
                    if not note_id:
                        continue
                    
                    # 获取详情
                    note = await self._get_note_detail(note_id)
                    if note:
                        self.notes.append(note)
                        note_count += 1
                        print(f"  📄 [{note_count}] {note.title[:30]}...")
                    
                    # 请求间隔
                    await asyncio.sleep(self.request_interval)
                
                page_num += 1
    
    async def _crawl_by_note_ids(self):
        """
        通过指定笔记ID爬取
        """
        for i, note_id in enumerate(self.note_ids):
            print(f"📄 获取笔记 [{i+1}/{len(self.note_ids)}]: {note_id}")
            
            note = await self._get_note_detail(note_id)
            if note:
                self.notes.append(note)
            
            await asyncio.sleep(self.request_interval)
    
    async def _crawl_by_creators(self):
        """
        通过创作者主页爬取
        """
        # TODO: 实现创作者主页爬取
        pass
    
    async def _get_note_detail(self, note_id: str) -> Optional[XHSNote]:
        """
        获取笔记详情（含评论）
        
        Args:
            note_id: 笔记ID
        
        Returns:
            笔记对象
        """
        try:
            # 获取详情
            result = await self.client.get_note_detail(note_id)
            
            # 解析数据
            note_data = result.get("data", {}).get("items", [{}])[0].get("note_card", {})
            
            # 构建用户对象
            user_data = note_data.get("user", {})
            user = XHSUser(
                user_id=user_data.get("user_id", ""),
                nickname=user_data.get("nickname", ""),
                avatar=user_data.get("image", ""),
                desc=user_data.get("desc", ""),
                ip_location=user_data.get("ip_location", ""),
            )
            
            # 构建笔记对象
            note = XHSNote(
                note_id=note_id,
                title=note_data.get("title", ""),
                desc=note_data.get("desc", ""),
                note_type=note_data.get("type", "normal"),
                time=note_data.get("time", ""),
                liked_count=note_data.get("interact_info", {}).get("liked_count", 0),
                collected_count=note_data.get("interact_info", {}).get("collected_count", 0),
                comment_count=note_data.get("interact_info", {}).get("comment_count", 0),
                share_count=note_data.get("interact_info", {}).get("share_count", 0),
                user=user,
                ip_location=note_data.get("ip_location", ""),
            )
            
            # 获取图片
            image_list = note_data.get("image_list", [])
            note.images = [img.get("url_default", "") for img in image_list]
            
            # 获取视频
            if note.note_type == "video":
                video_data = note_data.get("video", {})
                note.video_url = video_data.get("media", {}).get("stream", {}).get("h264", [{}])[0].get("master_url", "")
            
            # 爬取评论
            if self.enable_comments and note.comment_count > 0:
                note.comments = await self._get_comments(note_id)
            
            return note
            
        except XHSApiException as e:
            print(f"  ❌ 获取笔记失败: {e}")
            return None
    
    async def _get_comments(self, note_id: str) -> List[XHSComment]:
        """
        获取笔记评论
        
        Args:
            note_id: 笔记ID
        
        Returns:
            评论列表
        """
        comments = []
        cursor = ""
        
        while len(comments) < self.max_comments:
            try:
                result = await self.client.get_note_comments(
                    note_id=note_id,
                    cursor=cursor
                )
                
                comment_list = result.get("data", {}).get("comments", [])
                if not comment_list:
                    break
                
                for comment_data in comment_list:
                    # 构建用户对象
                    user_data = comment_data.get("user", {})
                    user = XHSUser(
                        user_id=user_data.get("user_id", ""),
                        nickname=user_data.get("nickname", ""),
                        avatar=user_data.get("image", ""),
                    )
                    
                    # 构建评论对象
                    comment = XHSComment(
                        comment_id=comment_data.get("id", ""),
                        content=comment_data.get("content", ""),
                        create_time=comment_data.get("create_time", ""),
                        ip_location=comment_data.get("ip_location", ""),
                        liked_count=comment_data.get("like_count", 0),
                        user=user,
                    )
                    
                    # 获取二级评论
                    if self.enable_sub_comments:
                        sub_comment_count = comment_data.get("sub_comment_count", 0)
                        if sub_comment_count > 0:
                            comment.sub_comments = await self._get_sub_comments(comment.comment_id)
                    
                    comments.append(comment)
                
                # 获取下一页游标
                cursor = result.get("data", {}).get("cursor", "")
                has_more = result.get("data", {}).get("has_more", False)
                
                if not has_more:
                    break
                
                await asyncio.sleep(self.request_interval)
                
            except XHSApiException as e:
                print(f"  ⚠️ 获取评论失败: {e}")
                break
        
        return comments
    
    async def _get_sub_comments(self, root_comment_id: str) -> List[XHSComment]:
        """
        获取二级评论
        
        Args:
            root_comment_id: 根评论ID
        
        Returns:
            二级评论列表
        """
        sub_comments = []
        cursor = ""
        
        try:
            result = await self.client.get_sub_comments(
                root_comment_id=root_comment_id,
                cursor=cursor
            )
            
            sub_comment_list = result.get("data", {}).get("comments", [])
            
            for sub_data in sub_comment_list:
                user_data = sub_data.get("user", {})
                user = XHSUser(
                    user_id=user_data.get("user_id", ""),
                    nickname=user_data.get("nickname", ""),
                )
                
                sub_comment = XHSComment(
                    comment_id=sub_data.get("id", ""),
                    content=sub_data.get("content", ""),
                    create_time=sub_data.get("create_time", ""),
                    user=user,
                )
                
                sub_comments.append(sub_comment)
        
        except XHSApiException as e:
            print(f"  ⚠️ 获取二级评论失败: {e}")
        
        return sub_comments
    
    async def _save_data(self):
        """
        保存数据到文件
        """
        output_dir = Path("data/xhs")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 转换为字典列表
        data = []
        for note in self.notes:
            note_dict = {
                "note_id": note.note_id,
                "title": note.title,
                "desc": note.desc,
                "type": note.note_type,
                "video_url": note.video_url,
                "images": note.images,
                "time": note.time,
                "liked_count": note.liked_count,
                "collected_count": note.collected_count,
                "comment_count": note.comment_count,
                "share_count": note.share_count,
                "user": {
                    "user_id": note.user.user_id if note.user else "",
                    "nickname": note.user.nickname if note.user else "",
                } if note.user else {},
                "ip_location": note.ip_location,
                "comments": [
                    {
                        "comment_id": c.comment_id,
                        "content": c.content,
                        "create_time": c.create_time,
                        "ip_location": c.ip_location,
                        "liked_count": c.liked_count,
                        "user": {
                            "user_id": c.user.user_id if c.user else "",
                            "nickname": c.user.nickname if c.user else "",
                        } if c.user else {},
                    }
                    for c in note.comments
                ]
            }
            data.append(note_dict)
        
        # 保存JSON
        output_file = output_dir / f"xhs_notes_{int(time.time())}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 数据已保存到: {output_file}")


# 使用示例
async def main():
    crawler = XHSCrawler(
        keywords=["游戏", "原神"],
        enable_comments=True,
        enable_sub_comments=True,
        max_notes=10,
        max_comments=50,
        headless=True,
    )
    await crawler.start()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 六、其他平台爬虫实现要点

### 6.1 抖音爬虫 (douyin/)

```python
# 抖音API端点
API_BASE = "https://www.douyin.com"
SEARCH_URL = f"{API_BASE}/aweme/v1/web/search/"
VIDEO_DETAIL_URL = f"{API_BASE}/aweme/v1/web/aweme/detail/"
COMMENT_URL = f"{API_BASE}/aweme/v1/web/comment/list/"

# 抖音签名参数
# 需要获取: a_bogus, ms_token, ttwid
# 签名函数: window.byted_acrawler.sign
```

### 6.2 快手爬虫 (kuaishou/)

```python
# 快手API端点
API_BASE = "https://www.kuaishou.com"
SEARCH_URL = f"{API_BASE}/graphql"
VIDEO_DETAIL_URL = f"{API_BASE}/short-video/photo"

# 快手使用GraphQL接口
# 签名参数: kpn, kpf, userId
```

### 6.3 B站爬虫 (bilibili/)

```python
# B站API端点
API_BASE = "https://api.bilibili.com"
SEARCH_URL = f"{API_BASE}/x/web-interface/search/type"
VIDEO_DETAIL_URL = f"{API_BASE}/x/web-interface/view"
COMMENT_URL = f"{API_BASE}/x/v2/reply"

# B站签名参数: wbi签名
# 签名函数: window.__INITIAL_STATE__.wbi
```

### 6.4 微博爬虫 (weibo/)

```python
# 微博API端点
API_BASE = "https://weibo.com"
SEARCH_URL = f"{API_BASE}/ajax/search/type"
STATUS_URL = f"{API_BASE}/ajax/statuses/show"
COMMENT_URL = f"{API_BASE}/ajax/statuses/buildComments"

# 微博需要Cookie中的SUB参数
```

---

## 七、运行命令汇总

```bash
# 小红书关键词搜索
uv run main.py --platform xhs --lt qrcode --type search

# 小红书指定帖子
uv run main.py --platform xhs --lt qrcode --type detail

# 抖音关键词搜索
uv run main.py --platform dy --lt qrcode --type search

# B站关键词搜索
uv run main.py --platform bili --lt qrcode --type search

# 微博关键词搜索
uv run main.py --platform wb --lt qrcode --type search

# 查看帮助
uv run main.py --help
```

---

## 八、常见问题与解决方案

### 8.1 登录失败

```python
# 问题：二维码不显示或登录失败
# 解决：关闭无头模式
HEADLESS = False

# 重新登录：删除登录态缓存
rm -rf browser_data/xhs/
```

### 8.2 签名获取失败

```python
# 问题：签名参数为空
# 原因：页面未完全加载
# 解决：等待页面加载完成
await page.wait_for_load_state("networkidle")
```

### 8.3 请求被限制

```python
# 问题：请求频率过高被封
# 解决：增加请求间隔
CRAWLER_REQUEST_INTERVAL = 2.0  # 增加到2秒

# 或使用代理池
ENABLE_IP_PROXY = True
```

### 8.4 数据为空

```python
# 问题：爬取数据为空
# 检查项：
# 1. 是否已登录成功
# 2. 关键词是否正确
# 3. 是否有反爬限制
```

---

## 九、项目依赖 (requirements.txt)

```txt
playwright>=1.40.0
aiohttp>=3.9.0
aiofiles>=23.2.0
pydantic>=2.0.0
python-dotenv>=1.0.0
aiomysql>=0.2.0
pandas>=2.0.0
```

---

## 十、总结

### 核心技术要点

1. **Playwright浏览器自动化** - 模拟真实用户操作
2. **登录态持久化** - 一次登录，多次使用
3. **JS表达式获取签名** - 无需逆向加密算法
4. **异步并发爬取** - 提高效率

### 与传统爬虫对比

| 对比项 | 传统爬虫 | MediaCrawler |
|--------|---------|--------------|
| 签名获取 | 逆向JS算法 | 浏览器执行JS |
| 技术门槛 | 高 | 低 |
| 维护成本 | 高（平台更新需重新逆向） | 低（自动适配） |
| 稳定性 | 一般 | 较高 |
| 性能 | 高 | 中等（需要浏览器） |

---

**文档版本**: v1.0  
**更新日期**: 2026-03-23  
**参考项目**: https://github.com/NanmiCoder/MediaCrawler
