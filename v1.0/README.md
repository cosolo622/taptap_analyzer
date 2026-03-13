# TapTap评价分析工具 v1.0

## 版本信息

- **版本号**: v1.0
- **发布日期**: 2026-03-10
- **开发者**: Trae AI

---

## 功能概述

TapTap游戏评价爬取与分析工具，支持：

1. **爬取TapTap游戏评价** - 使用Selenium爬取评价内容、星级、日期、用户名、游戏时长、设备信息
2. **情感分析** - 使用GLM大模型进行精准情感识别（正向/中性/负向）
3. **问题分类** - 智能识别评价中的问题类型（环境问题、技术问题、商业化问题等）
4. **Excel报告生成** - 自动生成包含评价明细、情感分布、问题分类统计的Excel报告

---

## 文件结构

```
v1.0/
├── README.md                    # 本文档
├── code/                        # 核心代码
│   ├── selenium_crawler.py      # 爬虫核心模块
│   ├── run_goose_duck.py        # 鹅鸭杀专用运行脚本
│   ├── sentiment_analyzer.py    # 情感分析模块
│   ├── classifier.py            # 分类器模块
│   ├── excel_exporter.py        # Excel导出模块
│   └── requirements.txt         # 依赖列表
├── output/                      # 输出结果
│   └── 鹅鸭杀_GLM分析_v1.0.xlsx  # v1.0版本分析结果
└── docs/                        # 文档
    └── 开发踩坑记录.md           # 详细踩坑记录
```

---

## 开发过程

### 第一阶段：爬虫开发

1. **初始方案**: 使用requests直接请求TapTap API
   - 结果: API返回404，需要登录态和特殊headers

2. **第二方案**: 使用Selenium模拟浏览器
   - 成功爬取评价内容
   - 遇到问题: 星级和日期解析错误

### 第二阶段：数据解析优化

1. **星级解析问题**
   - 问题: 页面有10个星星SVG，前5暗后5亮，无法区分不同星级
   - 解决: 发现星级通过`review-rate__highlight`的`width`属性控制
   - 计算公式: 星级 = width / 18 (每个星星宽度18px)

2. **日期解析问题**
   - 问题: 部分评价显示"20小时前"等相对时间
   - 解决: 从`title`属性获取完整日期（格式：2026/02/26 21:48:26）

### 第三阶段：情感分析优化

1. **传统方案问题**
   - 使用关键词匹配进行情感分析和分类
   - 问题: 纯正向评价被错误标记为"太氪金"、"bug多"等负面标签

2. **GLM大模型方案**
   - 使用GLM直接分析每条评价
   - 输出: 情感、问题分类、一句话摘要
   - 效果: 准确识别情感，精准提取问题

---

## 踩坑记录

### 1. 星级解析坑

**问题描述**:
- 页面显示5个星星，但HTML中有10个SVG元素
- 前5个是灰色背景，后5个是实际评分
- 通过SVG的fill颜色判断星级，但所有评价的后5个都是青色

**解决方案**:
```python
# 错误方式: 统计亮色星星数量
bright_count = sum(1 for svg in star_svgs if 'rgb(0, 217, 197)' in fill)

# 正确方式: 从highlight的width计算星级
highlight = elem.find_element(By.CSS_SELECTOR, '.review-rate__highlight')
width = int(re.search(r'width:\s*(\d+)px', style).group(1))
rating = round(width / 18)  # 每个星星18px
```

### 2. 日期解析坑

**问题描述**:
- 部分评价显示"20小时前"、"3天前"等相对时间
- 直接解析文本会导致日期不准确

**解决方案**:
```python
# 从title属性获取完整日期
time_elem = elem.find_element(By.CSS_SELECTOR, '.tap-time')
title = time_elem.get_attribute('title')  # "2026/02/26 21:48:26"
date_match = re.match(r'(\d{4})/(\d{2})/(\d{2})', title)
```

### 3. 情感分析坑

**问题描述**:
- 传统关键词匹配对正向评价误判严重
- 例如: "游戏很好玩，角色可爱"被标记为"商业化问题-太氪金"

**解决方案**:
- 使用GLM大模型直接分析
- Prompt设计:
```
你是一个游戏评价分析专家。请分析以下游戏评价：
1. 情感: 正向/中性/负向
2. 问题分类: 如果有问题，列出具体问题类型
3. 一句话摘要: 总结评价核心内容
```

### 4. 内容过滤坑

**问题描述**:
- 爬取的内容包含用户名、游戏时长等元数据
- 需要过滤这些干扰信息

**解决方案**:
```python
# 过滤用户名和游戏时长
content = re.sub(r'^[^\s]+\s*', '', content)  # 移除开头的用户名
content = re.sub(r'玩过\s*$', '', content)    # 移除结尾的"玩过"
```

---

## 依赖安装

```bash
pip install selenium
pip install webdriver-manager
pip install pandas
pip install openpyxl
pip install jieba
pip install snownlp
```

---

## 使用方法

### 1. 爬取评价

```python
from selenium_crawler import TapTapCrawler

crawler = TapTapCrawler()
reviews = crawler.crawl_reviews(
    app_id=258720,  # 鹅鸭杀
    max_reviews=200,
    max_scrolls=20
)
```

### 2. 分析评价

```python
# 使用GLM分析（推荐）
# 直接调用GLM API或手动分析

# 使用传统方式分析
from sentiment_analyzer import SentimentAnalyzer
from classifier import ReviewClassifier

analyzer = SentimentAnalyzer()
classifier = ReviewClassifier()

for review in reviews:
    sentiment = analyzer.analyze(review['content'])
    issues = classifier.classify(review['content'])
```

### 3. 导出Excel

```python
from excel_exporter import ExcelExporter

exporter = ExcelExporter()
exporter.export(reviews, '鹅鸭杀_评价分析.xlsx')
```

---

## v1.0版本分析结果

### 数据概览

| 指标 | 数值 |
|------|------|
| 总评价数 | 200条 |
| 平均星级 | 4.18 |

### 情感分布

| 情感 | 数量 | 占比 |
|------|------|------|
| 正向 | 154条 | 77.0% |
| 负向 | 22条 | 11.0% |
| 中性偏负 | 18条 | 9.0% |
| 中性 | 6条 | 3.0% |

### 问题分类TOP10

| 排名 | 问题分类 | 出现次数 |
|------|----------|----------|
| 1 | 环境问题-低素质玩家 | 3次 |
| 2 | 环境问题-路人局体验差 | 3次 |
| 3 | 环境问题-玩家素质差 | 3次 |
| 4 | 匹配机制问题 | 2次 |
| 5 | 环境问题-语言攻击 | 2次 |

---

## 后续优化方向

1. **爬虫优化**
   - 支持更多评价来源（App Store、Google Play等）
   - 增加反爬策略（代理IP、随机延迟等）

2. **分析优化**
   - 支持批量调用GLM API自动化分析
   - 增加更多问题分类维度
   - 支持自定义分类标签

3. **报告优化**
   - 增加可视化图表
   - 支持PDF导出
   - 增加竞品对比分析

---

## 更新日志

### v1.0 (2026-03-10)
- 初始版本发布
- 完成TapTap评价爬取功能
- 完成GLM情感分析功能
- 完成Excel报告生成功能
- 修复星级解析问题
- 修复日期解析问题
- 优化情感分析准确率
