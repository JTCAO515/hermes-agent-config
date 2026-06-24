# Python f-string + JavaScript 花括号冲突

## 问题

在 Python f-string 中嵌入 JavaScript 代码时，JS 的 `{` 和 `}` 会被 Python 解析器误认为 f-string 表达式定界符，导致 `SyntaxError: f-string: invalid syntax`。

## 触发条件

Python 3.11 及更早版本的 f-string 解析器在看到 `{` 时会尝试将后面内容解析为 Python 表达式。当 JS 代码例如 `function() {` 出现时，Python 尝试将 `{var r=...}` 解析为表达式 → 失败。

## 解决方案

### 方案 A：字符串拼接（推荐）

将 JS 代码移出 f-string，用字符串拼接：

```python
html = f'''...<div>{variable}</div>...'''
html += '''<script>
var x = function() {
  // JS code with curly braces
  if (condition) { doSomething(); }
};
</script>'''
```

### 方案 B：先赋值变量

```python
js_code = """<script>
var x = function() {
  if (condition) { doSomething(); }
};
</script>"""
html = f'''<html>{variable}</html>''' + js_code
```

### 方案 C：用 `.replace()` 注入变量

```python
html = '''<html>__VAR__</html>
<script>var x = function() { if (true) {} };</script>'''
html = html.replace('__VAR__', variable_value)
```

## Python 版本差异

| 版本 | f-string 限制 | 说明 |
|------|--------------|------|
| Python 3.11 | 严格 | `{` `}` 必须是有效表达式或 `{{` `}}` |
| Python 3.12+ | 宽松 (PEP 701) | 允许嵌套引号和更多语法 |

如果在 Vercel 部署（`.python-version` 指定 3.12），本地开发用 3.11 可能会有不一致行为。
