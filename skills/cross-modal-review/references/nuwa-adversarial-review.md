# NUWA API Adversarial Code Review

> 本文件记录了使用 NUWA 中转 API（api.nuwaflux.com）进行跨模型对抗式代码审查的技术方案。

## 适用场景

- 当客户要求使用特定模型（如 GPT 5.5、Gemini 3.5）而非当前主模型做代码审查时
- 当需要真正意义上的跨模型审查（不同提供商的模型各自审查同一份代码，对比结果）
- 当 `delegate_task` 子代理路由未配置目标模型时，作为降级方案

## 前提条件

- NUWA API Key 已配置在 `~/.hermes/.env` 中（`NUWAFLUX_API_KEY`）
- 目标模型在 NUWA 端点可用（`GET https://api.nuwaflux.com/v1/models` 查询）

## 代理问题

NUWA API 部署在中国境外。如果服务器配置了 HTTP 代理（`http_proxy`），必须绕过：

```python
import httpx
client = httpx.Client(verify=False)  # verify=False 仅用于测试环境
```

**关键陷阱：** 环境变量 `http_proxy` / `https_proxy` 会被 `httpx`、`urllib`、`requests` 等库自动读取。即使设置 `NO_PROXY=*`，某些版本的 `httpx` 仍会走代理。解决方案是用 `httpx.Client(verify=False)` 创建无代理客户端。

## 模型列表发现

```python
import httpx, json
client = httpx.Client(verify=False)
resp = client.get(
    'https://api.nuwaflux.com/v1/models',
    headers={'Authorization': f'Bearer {NUWAFLUX_API_KEY}'},
    timeout=30
)
models = [m['id'] for m in resp.json().get('data', [])]
```

截至 2026-06，可用的大模型（部分）：

| 供应商 | 可用模型 |
|--------|----------|
| OpenAI | `gpt-5.5`, `gpt-5.5-pro`, `gpt-5.4`, `gpt-5.3-chat-latest`, `gpt-5.2`, `gpt-5.1`, `gpt-5` |
| Google | `gemini-3.5-flash`, `gemini-2.5-pro`, `gemini-2.5-flash` |
| Anthropic | `claude-opus-4-8`, `claude-sonnet-4-6`, `claude-haiku-4-5` |

## 对抗式审查的 Prompt 设计

### 系统提示词核心要素

```
You are {MODEL_NAME} — a hyper-critical adversarial code reviewer.
Find EVERY bug, math error, logic flaw, security issue, performance problem.
Be ruthless. Do not hold back.

Format each issue as:
### [CRITICAL|HIGH|MEDIUM|LOW] [file.py:LINENUM] Title
- What the code does
- What's wrong
- Correct approach
- Impact on end users

You MUST find at least 3 CRITICAL issues.
End with a score table across 6 dimensions and a one-sentence verdict.
```

### 双模型对比输出格式

```python
print(f"""
## 双模型审查对比

| 维度 | {model_a} | {model_b} | 差异 |
|------|-----------|-----------|------|
| 数学正确性 | ... | ... | ... |
| 逻辑完整性 | ... | ... | ... |
| 安全性 | ... | ... | ... |

### 共识问题（两模型一致指出）
- EV 公式错误 ✅✅
- ...

### 分歧问题
- {model_a}发现但{model_b}没发现: ...
- {model_b}发现但{model_a}没发现: ...
""")
```

## 注意事项

- 不同模型的审查严格度差异巨大（GPT 5.5 比 GLM 5.1 在数学维度上更严格）
- 两个模型一致判定为 CRITICAL 的问题 = 真正最重要的 bug
- NUWA API 模型名不带 `-turbo` 后缀（`gpt-5.5` ✅，`gpt-5.5-turbo` ❌）
- 当前 `delegate_task` 无法直接路由到 GLM/NUWA——详见 AGENTS.md 中的 provider 配置限制
- 建议将审查输出保存到临时文件，以便在审查完成后对比分析

## 双模型独立审查 + 交叉对比工作流

这是本 session 实战验证的有效模式：两个模型**各自独立审查同一份代码**（非链式审查），然后系统性地交叉对比发现。

### 核心原则

```
两个单独做，不要一个审另一个。
独立审查能发现不同角度的问题。
交叉对比能揭示真正最重要的问题（共识 = 高可信）。
```

### 工作流

1. **Phase A: 第一模型审查** — 用第一个模型（如 GLM 5.1）全面审查代码，按维度打分
2. **Phase B: 第二模型审查** — 用第二个模型（如 GPT 5.5）独立审查**同一份代码**，给出独立评分
3. **Phase C: 交叉对比分析** — 系统性地对比两套审查结果，生成合并报告

### 交叉对比输出格式

#### 1. 双模型发现对比表

```
### [模型A] 发现但 [模型B] 没抓到的 N 个问题

| # | 问题 | 严重度 | 文件 |
|---|------|--------|------|
| 1 | `encode_card` 文档声称编码范围 0-51，实际产生 2-62 | HIGH | card.py:54 |
| 2 | ... | ... | ... |

### [模型B] 发现但 [模型A] 没抓到的 N 个问题

| # | 问题 | 严重度 | 文件 |
|---|------|--------|------|
| 1 | `PRIMES` 质数表声明但从未使用——过期文档 | LOW | card.py:48 |
| 2 | ... | ... | ... |
```

#### 2. 核心共识表（两模型一致判定）

```
### 核心共识（双模型一致判定为 CRITICAL 的）

| 问题 | 模型A | 模型B | 真·优先级 |
|------|-------|-------|----------|
| ❌ EV 公式 Win$=pot+call 双倍计入跟注额 | ✅ CRITICAL | ✅ CRITICAL | **P0** |
| ❌ ... | ✅ CRITICAL | ✅ HIGH | **P0** |
```

**共识判断规则：**
- 两模型都判定为 CRITICAL → **P0**（最高优先级）
- 一个 CRITICAL + 一个 HIGH → **P0**
- 两个 HIGH → **P1**
- 仅一个模型发现 → 按该模型的严重度，但标记为待验证

#### 3. 维度评分对比表

```
### 打分对比

| 维度 | 模型A | 模型B | 差异 |
|------|-------|-------|------|
| 数学正确性 | 0/2 | 2/10 | 模型B更严格 |
| 逻辑完整性 | 0/2 | 4/10 | ~ |
| 安全性 | +1/2 | 4/10 | 模型B发现async阻塞式DoS漏洞 |
| 性能 | 0/2 | 3/10 | 都批评串行+假文档 |
| 可维护性 | +1/2 | 5/10 | ~ |
| 实战可用性 | -1/2 | 2/10 | 都认为对抗随机牌没用 |
| **总计** | **1/12** | **20/60** | ~ |
```

**注意：** 不同模型的评分标准差异巨大——不要直接比较分数绝对值，比较**相对趋势**（哪些维度两模型都打低分）。

#### 4. 优先级修复清单

```
### 立即修复 Top N（基于双模型共识）

| 优先级 | 问题 | 共识等级 | 文件 |
|--------|------|----------|------|
| 🔴 P0 | EV 公式中 Win$ 定义错误 | 双模型CRITICAL | decision_engine.py:83 |
| 🔴 P0 | 蒙特卡洛胜率统计对有偏 | 双模型CRITICAL | equity_calculator.py:36 |
| 🟠 P1 | 串行循环无并行，手机端4秒延迟 | 双模型HIGH | equity_calculator.py:134 |
```

#### 5. 模型判词

```
### [模型A] 一句话判词

> "This is a nice-looking prototype wrapped around broken poker math;
> do not trust its decisions for real money."
```

### 何时使用双模型 vs 单模型

- **双模型交叉对比**：重大代码审计、安全敏感变更、数学计算密集型应用、用户明确要求多模型审查
- **单模型审查**：快速日常代码审查、小改动、非关键代码

### 这个模式捕捉不到的

双模型独立审查 + 交叉对比能大幅降低假阳性和漏检率，但仍有盲区：
- 两模型可能**同时遗漏**同一类问题（如都忽视代码风格问题）
- 共识不等于正确——两模型可能对某个问题判断一致但都错了
- 测试数据（单元测试覆盖）仍是最终验证手段，不能替代
