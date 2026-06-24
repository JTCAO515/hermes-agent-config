# Aliyun SMS Integration

> 阿里云短信服务 API 集成。通过 dysmsapi.aliyuncs.com 的 HTTP GET 请求 + HMAC-SHA1 签名发送短信。

## 环境变量

| 变量 | 说明 | 获取方式 |
|------|------|----------|
| `SMS_PROVIDER` | `"console"` 或 `"aliyun"` | 设 `"aliyun"` 启用 |
| `ALIYUN_SMS_ACCESS_KEY` | Access Key ID | RAM 用户 AccessKey |
| `ALIYUN_SMS_SECRET` | Access Key Secret | RAM 用户 AccessKey |
| `ALIYUN_SMS_SIGN_NAME` | 短信签名（如 "VisePanda"） | 阿里云短信 -> 签名管理 |
| `ALIYUN_SMS_TEMPLATE_CODE` | 模板编号（如 `SMS_123456789`） | 阿里云短信 -> 模板管理 |
| `ALIYUN_SMS_TEMPLATE_PARAM` | 模板变量 JSON（默认 `{"code":"%s"}`） | 按模板实际变量调整 |

## 签名算法

阿里云短信 API 使用 HMAC-SHA1 签名，完整流程：

```python
import hmac, base64, hashlib, urllib.parse, uuid

def _send_sms(phone: str, code: str) -> bool:
    params = {
        "Action": "SendSms",
        "Format": "JSON",
        "Version": "2017-05-25",
        "AccessKeyId": ALIYUN_SMS_ACCESS_KEY,
        "SignatureMethod": "HMAC-SHA1",
        "Timestamp": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "SignatureVersion": "1.0",
        "SignatureNonce": str(uuid.uuid4()),
        "PhoneNumbers": phone,
        "SignName": ALIYUN_SMS_SIGN_NAME,
        "TemplateCode": ALIYUN_SMS_TEMPLATE_CODE,
        "TemplateParam": ALIYUN_SMS_TEMPLATE_PARAM % code,
    }
    sorted_keys = sorted(params.keys())
    query = "&".join(f"{k}={urllib.parse.quote(str(params[k]), safe='')}" for k in sorted_keys)
    string_to_sign = f"GET&{urllib.parse.quote('/', safe='')}&{urllib.parse.quote(query, safe='')}"
    sig = base64.b64encode(
        hmac.new(f"{ALIYUN_SMS_SECRET}&".encode(), string_to_sign.encode(), hashlib.sha1).digest()
    ).decode()
    url = f"https://dysmsapi.aliyuncs.com/?{query}&Signature={urllib.parse.quote(sig, safe='')}"
    r = httpx.get(url, timeout=10)
    result = r.json()
    return result.get("Code") == "OK"
```

## 调试

- `result["Code"] != "OK"` 时，`result["Message"]` 包含错误描述
- 常见错误：
  - `InvalidAccessKeyId.NotFound` — AccessKey 不存在
  - `SignatureDoesNotMatch` — 签名计算错误（检查编码顺序）
  - `isv.BUSINESS_LIMIT_CONTROL` — 发送频率超限（同一号码 1 条/分钟）
  - `isv.OUT_OF_SERVICE` — 余额不足
