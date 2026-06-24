# pydantic-core glibc 兼容性 & 版本锁定

## 问题

Vercel Python 3.11 Lambda 使用 Amazon Linux 2 → **glibc 2.26**。

`pydantic-core` 是 Rust 二进制（`.so` 文件）。较新版本可能使用 `manylinux_2_28` 或更高 wheel 标签 → 要求 glibc ≥ 2.28 → **Lambda 上运行时报错**（FUNCTION_INVOCATION_FAILED，构建阶段 pip install 成功但运行时加载 .so 失败）。

## 已知兼容版本（2026-06 验证）

| 包 | 版本 | pydantic-core 版本 | glibc 要求 | Lambda 兼容 |
|---|------|-------------------|-----------|------------|
| pydantic | 2.10.6 | 2.27.2 (manylinux_2_17) | ≥ 2.17 | ✅ |
| pydantic | 2.11+ | 2.33+ | ≥ 2.28? | ⚠️ 未验证 |

## 锁定策略

```txt
# requirements.txt
fastapi==0.115.6
pydantic==2.10.6
```

**原则**：
- 用 `==` 完全锁定，**不用 `>=`**
- fastapi 锁定到 0.115.x 系列（2024-12 发布）
- pydantic 锁定到 2.10.x 系列（pydantic-core 2.27.x）

## 验证方法

```bash
python3 -m venv /tmp/test-venv
/tmp/test-venv/bin/pip install -q -r requirements.txt
/tmp/test-venv/bin/python -c "
import pydantic_core
print(f'pydantic-core version: {pydantic_core.__version__}')
import os
so_dir = os.path.dirname(pydantic_core.__file__)
for f in os.listdir(so_dir):
    if f.endswith('.so'):
        print(f'SO file: {f}')
"
```
