---
name: weread
description: >
  微信读书 (WeRead) API 接入。书架管理、书籍搜索、笔记/划线导出、书评、
  阅读统计。触发词：微信读书 / weread / 书架 / 读书笔记 / 划线 / 书评 /
  阅读记录 / 书籍搜索。当用户提到微信读书相关操作时加载此 Skill。
version: 1.0.0
---

# 微信读书 (WeRead) API 接入

通过微信读书 Web API 管理书架、导出笔记、搜索书籍、查看书评。

## 前置条件

Cookie 文件 `~/.hermes/.weread` 需包含：

```
wr_vid=12345678
wr_skey=xxxxxxxx
```

若未配置，引导用户从浏览器获取（见步骤 1）。

---

## 步骤 1：获取 Cookie

1. 打开 https://weread.qq.com/ 并微信扫码登录
2. F12 → Application → Cookies → `weread.qq.com`
3. 复制 `wr_vid` 和 `wr_skey` 的值
4. 写入 `~/.hermes/.weread`：
   ```
   wr_vid=你的vid
   wr_skey=你的skey
   ```

**验证凭证是否有效**：
```bash
source ~/.hermes/.weread
curl -s -b "wr_vid=$wr_vid; wr_skey=$wr_skey" \
  "https://i.weread.qq.com/user/notebooks" | python3 -m json.tool | head -20
```
若返回书架列表则凭证有效；返回 `{"errcode":-2012}` 则 Cookie 已过期。

---

## 步骤 2：API 速查

全部请求需带 `Cookie: wr_vid=...; wr_skey=...`，构造为 curl `-b` 参数。

### 书架
```bash
# 我的书架（所有书籍）
curl -s -b "$COOKIE" "https://i.weread.qq.com/shelf/sync?userVid=$WR_VID&synckey=0" | jq

# 最近阅读
curl -s -b "$COOKIE" "https://i.weread.qq.com/shelf/sync?userVid=$WR_VID&synckey=0&recent=1" | jq
```

### 书籍搜索
```bash
curl -s -b "$COOKIE" "https://i.weread.qq.com/book/search?query=三体" | jq
```

### 书籍详情
```bash
curl -s -b "$COOKIE" "https://i.weread.qq.com/book/info?bookId=BOOK_ID" | jq
```

### 目录
```bash
curl -s -b "$COOKIE" "https://i.weread.qq.com/book/chapter?bookId=BOOK_ID" | jq
```

### 笔记/划线（核心功能）
```bash
# 获取所有笔记本
curl -s -b "$COOKIE" "https://i.weread.qq.com/user/notebooks" | jq

# 某本书的笔记/划线
curl -s -b "$COOKIE" "https://i.weread.qq.com/book/bookmarklist?bookId=BOOK_ID" | jq

# 某条笔记的详细评论
curl -s -b "$COOKIE" "https://i.weread.qq.com/review/reviewlist?bookId=BOOK_ID&listType=1" | jq
```

### 阅读统计
```bash
curl -s -b "$COOKIE" "https://i.weread.qq.com/user/readtime?userVid=$WR_VID" | jq
```

### Agent Gateway（AI 功能）
```bash
# 书籍问答
curl -s -b "$COOKIE" \
  "https://i.weread.qq.com/api/agent/gateway" \
  -H "Content-Type: application/json" \
  -d '{"bookId":"BOOK_ID","input":"总结这本书的核心观点"}' | jq
```

---

## 步骤 3：常用操作

### 3.1 导出某本书的全部划线

```bash
source ~/.hermes/.weread && \
BOOK_ID="替换为书ID" && \
curl -s -b "wr_vid=$wr_vid; wr_skey=$wr_skey" \
  "https://i.weread.qq.com/book/bookmarklist?bookId=$BOOK_ID" | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
for item in data.get('updated', []):
    chapter = item.get('chapterUid', 0)
    text = item.get('markText', '')
    print(f'[{chapter}] {text}')
"
```

### 3.2 搜索并获取书 ID

```bash
source ~/.hermes/.weread && \
curl -s -b "wr_vid=$wr_vid; wr_skey=$wr_skey" \
  "https://i.weread.qq.com/book/search?query=关键词" | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
for book in data.get('books', []):
    info = book.get('bookInfo', {})
    print(f\"{info.get('bookId')} | {info.get('title')} | {info.get('author')}\")
"
```

### 3.3 导出所有书的所有笔记

```bash
source ~/.hermes/.weread
curl -s -b "wr_vid=$wr_vid; wr_skey=$wr_skey" \
  "https://i.weread.qq.com/user/notebooks" | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
for nb in data.get('books', []):
    book = nb.get('book', {})
    print(f\"=== {book.get('title', 'N/A')} ({book.get('bookId', 'N/A')}) ===\")
    print(f\"笔记数: {nb.get('noteCount', 0)}, 划线数: {nb.get('highlightCount', 0)}\")
    print()
"
```

---

## 常见问题

- **Cookie 过期**：`wr_skey` 约 30 天有效，过期需重新从浏览器获取
- **书 ID (bookId)**：可从书架 API 或搜索 API 获取，形如 `CB_DxW1AEABc`
- **分页**：部分接口支持 `offset` 参数
- **频率限制**：正常使用不会被限，避免高频循环请求

## 后续扩展

- [ ] 阅读报告生成（年度/月度）
- [ ] 笔记同步到脑库 (brain)
- [ ] 书评情感分析
- [ ] 书籍推荐
