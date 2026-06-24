# 功能添加/移除的多层同步模式

## 背景

WC26 项目（和其他 Vercel 单页应用）的前端功能跨越 4 层：HTML（结构）、JS（逻辑+渲染）、CSS（样式）、API（后端端点）。添加或移除一个功能时，**必须更新全部 4 层**，缺一不可。

## 移除功能模板（以 Chat 为例）

### HTML
1. 移除 Tab 按钮
2. 移除对应 `<section id="tab-xxx">` 整个区块

### JS
1. 移除所有功能相关的函数定义
2. 移除事件绑定监听器
3. 移除 Tab 切换 `switchTab` 中的 case

### CSS
1. 移除所有 `.chat-*` / `.功能-*` 样式类
2. 移除相关 `@keyframes` 动画定义

### API (Python)
1. 移除对应的 `if path == "/api/xxx"` 路由处理块
2. 如果功能模块是独立文件（如 `chat_engine.py`），路由移除后该文件保留也无害，但可删除减少部署包体积

## 添加功能模板

### HTML
1. 添加 Tab 按钮
2. 添加 `<section id="tab-xxx">` 区块（含所有静态 UI 元素）

### JS
1. 添加渲染函数（renderXxx）
2. 添加事件绑定
3. 添加 Tab 切换 case

### CSS
1. 添加所有 UI 样式类

### API (Python)
1. 添加路由处理块
2. 如需要独立模块，创建新 .py 文件
3. 从 index.py import

## 常见错误

- ❌ **只改 HTML 不改 JS** → Tab 按钮在但点击没反应
- ❌ **只改 JS 不改 CSS** → 元素渲染了但样式不对
- ❌ **只改前端不改 API** → 前端调用端点，后端 404
- ❌ **patch 同一大文件多次导致重复函数定义** → 在大型单文件 app 中（如 app.js 900 行），连续 patch 同一函数的临近区域可能产生重复代码。patch 后立即 `node --check app.js` 验证
