# English-Native Translation Convention

## Format Rule (Hard)
All Chinese text in data files follows this format:

```
"English text (中文)"
```

## Examples

| Context | Before | After |
|---------|--------|-------|
| Place name | `"name_zh": "北京"` | Keep — structured data |
| Place in UI | `"name": "北京王府井希尔顿"` | `"Hilton Beijing Wangfujing (北京王府井希尔顿)"` |
| Food in prompt | `[糖葫芦]($5)` | `candied hawthorns (糖葫芦, ¥5)` |
| Currency info | `¥13起步价 (flagfall)` | `¥13 starting fare (起步价/flagfall)` |
| Category title | `"title": "📄 必备证件"` | `"title": "📄 Essential Documents (必备证件)"` |
| Transport type | `"type": "高铁"` | `"type": "High-speed Rail (高铁)"` |
| Price key | `"故宫": 60` | `"Forbidden City (故宫)": 60` |
| Docstring | `"""价格估算引擎"""` | `"""Price estimation engine"""` |

## What NOT to translate
1. `name_zh` fields — they exist specifically to carry Chinese names
2. i18n `zh` sections — they support the language toggle feature
3. JS input-detection patterns — they match user keystrokes regardless of UI language
4. Cuisine `name_zh` / attraction `name_zh` — intentionally bilingual

## What to ALWAYS translate
1. Docstrings — these document the code for developers
2. AI system prompt examples — these generate user-facing output
3. Tool descriptions in data/tools — these are used by LLM to understand tool purpose
4. Button labels, placeholders, navigation — the UI itself
5. Price data dictionary keys — so code reads naturally
