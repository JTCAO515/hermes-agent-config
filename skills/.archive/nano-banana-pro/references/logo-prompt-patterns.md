# Logo / 品牌元素 Prompt 模式（gpt-image-2 经验）

> 2026-05-30 基于猪猪微熊猫头 Logo 迭代经验整理。使用模型 `gpt-image-2`。

## 核心原则

- **gpt-image-2 偏好具体风格描述而非抽象概念**。说"flat minimalist vector"比说"simple"效果好。
- **1024×1024 方图**最适合 logo 类生成。
- **base64 返回**（PNG 格式），需要 python3 解码保存。
- **URL 返回不稳定**，优先提取 `b64_json`。

## 成功 Prompt 模式

### 扁平极简矢量 Logo

```
[主体] logo, flat minimalist vector design, pure solid flat colors no gradients no shading,
clean crisp thin geometric lines, [风格] style with [配色] on [背景].
[s表情/姿态]. Simple flat silhouette style like a modern app icon or brand logo.
[额外属性]. Sharp clean edges, vector quality, no 3D, no textures.
```

### 参数填空

| 占位 | 示例值 |
|------|--------|
| 主体 | Panda head, Dragon silhouette, Phoenix crest |
| 风格 | cyberpunk tech, minimalist tech, neon retro, modern geometric |
| 配色 | bright cyan and neon green accents, electric blue and magenta |
| 背景 | dark charcoal background, pure black, white |
| 表情/姿态 | tilted slightly with a cocky half-smirk expression, one eyebrow raised, wearing a sideways cyber visor |
| 额外属性 | Circuit trace patterns forming the ears, geometric accent lines |

### 反模式（效果差）

- ❌ "cool" "awesome" — 太抽象，模型不理解
- ❌ "make it look professional" — 不如说具体的风格
- ❌ 把太多文字说明塞到 prompt 尾部 — 模型倾向于处理前面的描述
- ❌ 要求"Logo"但不说 "vector" — 容易生成写实渲染图

## 已知可用的 NUWA 端点

- 图片生成（gpt-image-2）：`POST https://api.nuwaflux.com/v1/images/generations`
- 模型列表：`GET https://api.nuwaflux.com/v1/models`
- 认证：`Authorization: Bearer $NUWA_API_KEY`
