# Agent 交接文档（2026-03-18）

## 一、改动目标

- 保持旧版功能不回退，补齐可上线的爬虫更新链路
- 提供自动更新与手动更新能力
- 支持新产品（含手动TapTap应用ID）接入和抓取

## 二、后端改动

- `v1.1/backend/main.py`
  - 移除重复 `/api/products` 路由定义冲突
  - 增加自动更新控制接口：
    - `POST /api/auto-update/start`
    - `POST /api/auto-update/stop`
    - `GET /api/auto-update/status`
  - `POST /api/crawler/start` / `incremental` / `fill-gaps` 改为真实后台线程执行
  - 新增统一任务状态日志写入逻辑（`crawler_status.logs`）
  - 产品搜索接口增加结果评分过滤，避免返回无关热门项

- `v1.1/backend/services/crawler_service.py`
  - 新增 `_resolve_game_id`：
    - 优先使用 `products.code` 的数字ID作为 TapTap app_id
    - 其次回退到内置 `TAPTAP_GAME_MAP`
  - `crawl_full/incremental/fill_gaps` 全部改为使用 `_resolve_game_id`

- `v1.1/backend/scheduler.py`
  - 修复导入错误，改为：
    - `from nlp.glm_analyzer import AliyunAnalyzer, TokenTracker`
  - 分析器实例化改为 `AliyunAnalyzer`

- `v1.1/backend/models/database.py`
  - 数据库口径明确为 PostgreSQL only
  - 非 `postgresql://` 连接串直接抛错

- `v1.1/backend/requirements.txt`
  - 补齐依赖：
    - `requests`
    - `playwright`
    - `apscheduler`

- `v1.1/backend/crawler/taptap_search_playwright.py`
  - 增加搜索结果评分排序与严格过滤逻辑

- `v1.1/backend/scripts/run_glm_sample20.py`（新增）
  - 抓取鹅鸭杀最新20条评价并调用GLM分析
  - 输出 `output/glm_sample20_*.json`

## 三、前端改动

- `v1.1/frontend/vite.config.js`
  - 优化版端口改为 `5622`
  - API代理目标改为 `http://localhost:8001`

- `v1.1/frontend/src/views/DataUpdate.vue`
  - 新增自动更新按钮：
    - 启动自动更新
    - 停止自动更新
  - 新增自动更新状态展示
  - 对接自动更新接口轮询

- `v1.1/frontend/src/views/ProductManage.vue`
  - 当搜索无结果时支持手动输入 TapTap 应用ID
  - 允许"名称 + code"直接添加产品，不依赖搜索结果

## 四、已验证结果

- 鹅鸭杀抓取与GLM分析可跑通（20条样本已产出JSON）
- 新产品"猫咪和汤（code=374994）"可添加并抓取成功
- 自动更新接口可启动/停止并返回状态

## 五、风险与注意

- GLM API存在网络超时，单批可能出现部分分析失败
- `search` 在TapTap网页侧偶发返回空，当前已支持手动ID兜底
- Windows下Playwright子进程偶发 `ValueError: I/O operation on closed pipe`，不影响主结果文件产出

## 六、建议下一步

- 给GLM调用加重试与指数退避，提升成功率
- 把自动更新间隔、最大抓取量做成前端可配置项并持久化
- 增加最小回归测试（crawler start/incremental/auto-update status）
