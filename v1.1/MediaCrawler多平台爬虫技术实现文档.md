# MediaCrawler 多平台爬虫技术实现文档

> 本文档详细记录MediaCrawler项目的技术实现，可作为独立实现多平台爬虫的完整指南。

---

## 一、项目概述

### 1.1 项目定位

MediaCrawler是一个基于Playwright浏览器自动化的多平台自媒体数据采集工具，核心特点：

- **无需JS逆向**：通过保留登录态的浏览器上下文获取签名参数
- **多平台支持**：小红书、抖音、快手、B站、微博、贴吧、知乎
- **全维度数据**：笔记内容、评论（含二级评论）、创作者信息、互动数据

### 1.2 技术架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MediaCrawler 整体架构                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    ┌─────────────┐                                                          │
│    │   main.py   │ ◀── 命令行入口，解析参数，调度爬虫                         │
│    └──────┬──────┘                                                          │
│           │                                                                 │
│           ▼                                                                 │
│    ┌─────────────────────────────────────────────────────────────────┐     │
│    │                    media_platform/                               │     │
│    │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │     │
│    │  │   xhs   │ │   dy    │ │   ks    │ │  bili   │ │   wb    │  │     │
│    │  │ 小红书   │ │  抖音   │ │  快手   │ │  B站    │ │  微博   │  │     │
│    │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘  │     │
│    │       │           │           │           │           │        │     │
│    │       └───────────┴───────────┴───────────┴───────────┘        │     │
│    │                               │                                 │     │
│    │                               ▼                                 │     │
│    │                    ┌─────────────────────┐                      │     │
│    │                    │   各平台通用组件      │                      │     │
│    │                    │  ┌───────────────┐  │                      │     │
│    │                    │  │   core.py     │  │◀─ 爬虫核心逻辑        │     │
│    │                    │  │   client.py   │  │◀─ API客户端封装       │     │
│    │                    │  │   login.py    │  │◀─ 登录处理            │     │
│    │                    │  │   field.py    │  │◀─ 数据模型定义        │     │
│    │                    │  │  *_sign.py    │  │◀─ 签名参数获取        │     │
│    │                    │  └───────────────┘  │                      │     │
│    │                    └─────────────────────┘                      │     │
│    └─────────────────────────────────────────────────────────────────┘     │
│                                    │                                        │
│                                    ▼                                        │
│    ┌─────────────────────────────────────────────────────────────────┐     │
│    │                        基础设施层                                 │     │
│    │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │     │
│    │  │  base/   │ │  store/  │ │  proxy/  │ │  cache/  │           │     │
│    │  │ 基础类   │ │  存储层  │ │ 代理池   │ │  缓存    │           │     │
│    │  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │     │
│    └─────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、环境搭建

### 2.1 系统要求

| 依赖项 | 版本要求 | 说明 |
|--------|----------|------|
| Python | ≥3.9, 推荐3.11 | 运行环境 |
| Node.js | ≥16.0.0 | 部分平台签名需要 |
| Playwright | 最新版 | 浏览器自动化 |

### 2.2 安装步骤

```bash
# 方式一：使用uv（推荐，更快）
# 安装uv
pip install uv

# 创建虚拟环境
uv venv --python 3.11

# 激活环境（Windows）
.venv\Scripts\activate

# 安装依赖
uv sync

# 安装浏览器驱动
uv run playwright install

# 方式二：使用原生Python
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
playwright install
```

### 2.3 项目结构

```
MediaCrawler/
├── main.py                    # 主入口
├── config/
│   └── base_config.py         # 核心配置文件
├── media_platform/            # 各平台实现
│   ├── xhs/                   # 小红书
│   │   ├── __init__.py
│   │   ├── core.py            # 爬虫核心逻辑
│   │   ├── client.py          # API客户端
│   │   ├── login.py           # 登录处理
│   │   ├── field.py           # 数据模型
│   │   ├── playwright_sign.py # Playwright签名获取
│   │   ├── xhs_sign.py        # 小红书签名算法
│   │   ├── exception.py       # 异常定义
│   │   ├── extractor.py       # 数据提取器
│   │   └── help.py            # 辅助函数
│   ├── douyin/                # 抖音
│   ├── kuaishou/              # 快手
│   ├── bilibili/              # B站
│   ├── weibo/                 # 微博
│   ├── tieba/                 # 贴吧
│   └── zhihu/                 # 知乎
├── base/                      # 庺础类
│   ├── base_crawler.py        # 爬虫基类
│   └── base_login.py          # 登录基类
├── store/                     # 存储层
│   ├── mysql_store.py         # MySQL存储
│   ├── csv_store.py           # CSV存储
│   └── json_store.py          # JSON存储
├── proxy/                     # 代理管理
│   └── proxy_ip_pool.py       # IP代理池
├── cache/                     # 缓存系统
│   └── browser_cache.py       # 浏览器登录态缓存
├── model/                     # 数据模型
│   └── m_xhs.py               # 小红书数据模型
├── browser_data/              # 登录态存储目录
│   └── xhs/
│       └── state.json         # 小红书登录态
└── data/                      # 爬取数据存储
    ├── xhs_note.csv
    └── xhs_comment.csv
```

---

## 三、核心配置详解

### 3.1 配置文件结构

```python
# config/base_config.py

# ==================== 平台配置 ====================
PLATFORM = "xhs"  # 可选: xhs, dy, ks, bili, wb, tieba, zhihu

# ==================== 登录配置 ====================
LOGIN_TYPE = "qrcode"  # 可选: qrcode(二维码), phone(手机号), cookie(Cookie)
HEADLESS = False       # 无头模式：登录时必须为False，爬取时可改为True

# ==================== 爬取配置 ====================
CRAWLER_TYPE = "search"  # 可选: search(关键词搜索), detail(指定帖子), creator(创作者主页)

# 关键词列表（search模式）
KEYWORDS = [
    "原神",
    "王者荣耀",
    "游戏攻略",
]

# 指定帖子ID列表（detail模式）
XHS_SPECIFIED_ID_LIST = [
    "note_id_1",
    "note_id_2",
]

# 创作者ID列表（creator模式）
XHS_CREATOR_ID_LIST = [
    "creator_id_1",
]

# ==================== 评论配置 ====================
ENABLE_GET_COMMENTS = True        # 是否爬取评论
ENABLE_GET_SUB_COMMENTS = True    # 是否爬取二级评论
MAX_COMMENTS_PER_NOTE = 100       # 每篇笔记最大评论数

# ==================== 数量限制 ====================
CRAWLER_MAX_NOTES = 50            # 最大爬取笔记数
CRAWLER_DOWNLOAD_MEDIA = False    # 是否下载图片/视频

# ==================== 代理配置 ====================
ENABLE_IP_PROXY = False           # 是否启用IP代理
IP_PROXY_POOL = []                # 代理池列表
IP_PROXY_POOL_API = ""            # 代理池API地址

# ==================== 存储配置 ====================
SAVE_DATA_OPTION = "csv"          # 可选: csv, json, mysql

# MySQL配置（如果选择mysql存储）
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "password"
MYSQL_DATABASE = "media_crawler"

# ==================== 浏览器配置 ====================
USER_DATA_DIR = "./browser_data"  # 登录态存储目录
BROWSER_TIMEOUT = 30000           # 浏览器超时时间(ms)
```

---

## 四、小红书爬虫实现详解

### 4.1 核心文件职责

| 文件 | 职责 | 核心类/函数 |
|------|------|-------------|
| `core.py` | 爬虫主逻辑 | `XHSCrawler`类 |
| `client.py` | API客户端 | `XHSClient`类 |
| `login.py` | 登录处理 | `XHSLogin`类 |
| `field.py` | 数据模型 | `XHSNote`, `XHSComment` |
| `playwright_sign.py` | 签名获取 | `PlaywrightSign`类 |

### 4.2 登录实现

```python
# media_platform/xhs/login.py

import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

class XHSLogin:
    """
    小红书登录处理类
    
    支持三种登录方式：
    1. qrcode: 二维码扫码登录（推荐）
    2. phone: 手机号+验证码登录
    3. cookie: 直接导入Cookie
    
    登录态存储：
    - 使用Playwright的storage_state功能持久化存储
    - 存储路径: browser_data/xhs/state.json
    """
    
    def __init__(self, config):
        """
        初始化登录处理器
        
        Args:
            config: 配置对象，包含登录相关参数
        """
        self.config = config
        self.browser_data_dir = Path(config.USER_DATA_DIR) / "xhs"
        self.browser_data_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.browser_data_dir / "state.json"
    
    async def login(self, browser: Browser) -> BrowserContext:
        """
        执行登录流程
        
        Args:
            browser: Playwright浏览器实例
        
        Returns:
            BrowserContext: 已登录的浏览器上下文
        """
        if self.config.LOGIN_TYPE == "qrcode":
            return await self._login_by_qrcode(browser)
        elif self.config.LOGIN_TYPE == "phone":
            return await self._login_by_phone(browser)
        elif self.config.LOGIN_TYPE == "cookie":
            return await self._login_by_cookie(browser)
        else:
            raise ValueError(f"不支持的登录方式: {self.config.LOGIN_TYPE}")
    
    async def _login_by_qrcode(self, browser: Browser) -> BrowserContext:
        """
        二维码扫码登录
        
        流程：
        1. 检查是否存在已保存的登录态
        2. 如果存在，直接加载
        3. 如果不存在，打开登录页等待扫码
        4. 扫码成功后保存登录态
        
        Returns:
            BrowserContext: 已登录的浏览器上下文
        """
        # 检查是否有已保存的登录态
        if self.state_file.exists():
            print(f"[登录] 发现已保存的登录态: {self.state_file}")
            context = await browser.new_context(
                storage_state=str(self.state_file),
                user_agent=self._get_user_agent()
            )
            # 验证登录态是否有效
            if await self._check_login_status(context):
                print("[登录] 登录态有效，直接使用")
                return context
            else:
                print("[登录] 登录态已失效，重新登录")
        
        # 创建新的浏览器上下文
        context = await browser.new_context(
            user_agent=self._get_user_agent()
        )
        page = await context.new_page()
        
        # 访问小红书首页
        print("[登录] 正在打开小红书...")
        await page.goto("https://www.xiaohongshu.com")
        
        # 等待页面加载
        await page.wait_for_load_state("networkidle")
        
        # 检查是否已登录
        if await self._check_login_status(context):
            print("[登录] 已登录状态")
            await self._save_login_state(context)
            return context
        
        # 点击登录按钮
        print("[登录] 请扫描二维码登录...")
        try:
            login_btn = await page.wait_for_selector(".login-btn", timeout=5000)
            await login_btn.click()
        except:
            pass  # 可能已经弹出二维码
        
        # 等待登录成功（检测登录状态变化）
        max_wait = 120  # 最长等待2分钟
        for i in range(max_wait):
            await asyncio.sleep(1)
            if await self._check_login_status(context):
                print(f"\n[登录] 登录成功！")
                await self._save_login_state(context)
                return context
            print(f"\r[登录] 等待扫码... ({i+1}s)", end="")
        
        raise TimeoutError("登录超时，请重新扫描二维码")
    
    async def _check_login_status(self, context: BrowserContext) -> bool:
        """
        检查登录状态
        
        通过访问需要登录的API来判断是否已登录
        
        Args:
            context: 浏览器上下文
        
        Returns:
            bool: 是否已登录
        """
        page = await context.new_page()
        try:
            # 访问用户信息接口
            await page.goto("https://edith.xiaohongshu.com/api/sns/web/v1/user/selfinfo")
            content = await page.content()
            # 如果返回了用户信息，说明已登录
            if "userInfo" in content or '"nickname"' in content:
                await page.close()
                return True
        except:
            pass
        finally:
            await page.close()
        return False
    
    async def _save_login_state(self, context: BrowserContext):
        """
        保存登录态
        
        Args:
            context: 浏览器上下文
        """
        await context.storage_state(path=str(self.state_file))
        print(f"[登录] 登录态已保存: {self.state_file}")
    
    def _get_user_agent(self) -> str:
        """
        获取User-Agent
        
        Returns:
            str: User-Agent字符串
        """
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
```

### 4.3 签名参数获取（核心创新）

```python
# media_platform/xhs/playwright_sign.py

import json
from playwright.async_api import Page, BrowserContext

class PlaywrightSign:
    """
    通过Playwright浏览器环境获取签名参数
    
    这是MediaCrawler的核心创新点：
    - 传统方式：逆向分析JS加密算法，成本高，维护难
    - MediaCrawler方式：在已登录的浏览器上下文中执行JS，直接获取签名
    
    原理：
    小红书的签名函数是平台内置的JS函数，在浏览器环境中可以调用
    我们只需要在正确的浏览器上下文中执行这个函数即可获得签名
    """
    
    def __init__(self, page: Page, context: BrowserContext):
        """
        初始化签名获取器
        
        Args:
            page: Playwright页面对象
            context: 浏览器上下文（包含登录态）
        """
        self.page = page
        self.context = context
    
    async def get_sign(self, url: str, data: dict = None) -> dict:
        """
        获取请求签名参数
        
        Args:
            url: 请求的URL
            data: 请求数据（POST请求时使用）
        
        Returns:
            dict: 签名参数，包含:
                - x-s: 签名字符串
                - x-t: 时间戳签名
                - x-s-common: 通用签名
        """
        # 构建签名参数
        sign_data = {
            "url": url,
            "data": data or {}
        }
        
        # 在浏览器中执行JS获取签名
        # 小红书的签名函数是 window._webmsxyw
        js_code = f"""
        () => {{
            try {{
                // 调用小红书内置的签名函数
                const signResult = window._webmsxyw(
                    '{url}',
                    {json.dumps(data) if data else 'null'}
                );
                return signResult;
            }} catch (e) {{
                console.error('签名获取失败:', e);
                return null;
            }}
        }}
        """
        
        result = await self.page.evaluate(js_code)
        
        if result:
            return {
                "x-s": result.get("x-s", ""),
                "x-t": result.get("x-t", ""),
                "x-s-common": result.get("x-s-common", ""),
            }
        
        # 如果签名函数不存在，尝试备用方案
        return await self._fallback_sign(url, data)
    
    async def _fallback_sign(self, url: str, data: dict) -> dict:
        """
        备用签名方案
        
        当主签名函数不可用时，尝试其他方式获取签名
        
        Args:
            url: 请求URL
            data: 请求数据
        
        Returns:
            dict: 签名参数
        """
        # 方案1：从网络请求中拦截签名
        # 方案2：使用本地签名算法（需要定期更新）
        # 这里简化处理，实际项目中需要更完善的备用方案
        return {}
    
    async def init_sign_environment(self):
        """
        初始化签名环境
        
        确保签名函数可用，如果不可用则注入
        """
        # 访问小红书页面，确保签名函数加载
        await self.page.goto("https://www.xiaohongshu.com")
        await self.page.wait_for_load_state("networkidle")
        
        # 检查签名函数是否存在
        has_sign_func = await self.page.evaluate("""
            () => {
                return typeof window._webmsxyw === 'function';
            }
        """)
        
        if not has_sign_func:
            print("[签名] 签名函数不存在，尝试注入...")
            # 这里可以注入签名算法，但通常不需要
            # 因为正常访问小红书页面后会自动加载
```

### 4.4 API客户端实现

```python
# media_platform/xhs/client.py

import json
import time
import uuid
import hashlib
from typing import Optional, Dict, List
from urllib.parse import urlencode
import aiohttp
from playwright.async_api import BrowserContext

class XHSClient:
    """
    小红书API客户端
    
    封装所有与小红书服务端交互的API请求
    每个请求都需要携带签名参数
    """
    
    # API基础地址
    BASE_URL = "https://edith.xiaohongshu.com"
    
    def __init__(
        self, 
        context: BrowserContext,
        sign_getter,  # PlaywrightSign实例
        timeout: int = 30
    ):
        """
        初始化API客户端
        
        Args:
            context: 浏览器上下文（包含登录态Cookie）
            sign_getter: 签名获取器
            timeout: 请求超时时间
        """
        self.context = context
        self.sign_getter = sign_getter
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def _get_cookies(self) -> str:
        """
        从浏览器上下文获取Cookie字符串
        
        Returns:
            str: Cookie字符串
        """
        cookies = await self.context.cookies()
        return "; ".join([f"{c['name']}={c['value']}" for c in cookies])
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        params: dict = None,
        data: dict = None
    ) -> dict:
        """
        发送API请求
        
        Args:
            method: 请求方法 GET/POST
            endpoint: API端点
            params: URL参数
            data: POST数据
        
        Returns:
            dict: 响应数据
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        # 获取签名参数
        sign_params = await self.sign_getter.get_sign(url, data or params)
        
        # 构建请求头
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://www.xiaohongshu.com",
            "Referer": "https://www.xiaohongshu.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
            "Cookie": await self._get_cookies(),
            # 签名参数
            "x-s": sign_params.get("x-s", ""),
            "x-t": sign_params.get("x-t", ""),
            "x-s-common": sign_params.get("x-s-common", ""),
        }
        
        # 发送请求
        if method.upper() == "GET":
            async with self.session.get(url, params=params,