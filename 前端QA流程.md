# 前端自动化QA流程

## 启动测试
```
mcp_Playwright_playwright_navigate: url=http://localhost:46635/, waitUntil=networkidle
```

## 等待加载
```
mcp_Playwright_playwright_evaluate: script="new Promise(r => setTimeout(() => r({title: document.title, len: document.body.innerHTML.length}), 3000))"
```

## 测试页面
```
mcp_Playwright_playwright_click: selector="菜单文字"
mcp_Playwright_playwright_evaluate: script="new Promise(r => setTimeout(() => r(document.querySelector('.xxx')?.innerText), 2000))"
```

## 检查错误
```
mcp_Playwright_playwright_console_logs: type=error, limit=20
```

## 验证API
```
mcp_Playwright_playwright_get: url=http://localhost:8000/api/xxx
```

## 核心原则
1. **先测试再交付**
2. **检查控制台错误**
3. **验证数据显示不是0**
4. **测试完整流程**

## 常见问题
- `el-statistic` 只支持数字，字符串用自定义div
- API参数设为可选（default=None）
- 检查路由是否冲突
