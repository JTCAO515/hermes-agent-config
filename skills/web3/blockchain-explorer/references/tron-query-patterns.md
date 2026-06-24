# TRON 查询模式速查

实际会话来源：查询 `60f5e0e44e9d5e446606db8b0c53025be5e23302ac9688c83715794459c826eb` 确认是 TRON USDT 转账。

## 核心差异

| 特性 | EVM | TRON |
|------|-----|------|
| 交易哈希前缀 | 带 `0x` | **不带 `0x`** |
| 地址格式(hex) | `0x` + 40 位 | `41` + 40 位 |
| 地址格式(base58) | — | `T` + 33 位 |
| 获取交易回执 | `eth_getTransactionReceipt` | `/wallet/gettransactioninfobyid` |
| 手续费 | `gasUsed × gasPrice` | `net_fee + energy_fee` |
| 时间戳位置 | 区块的 `timestamp` | 回执的 `blockTimeStamp` |

## API 端点

| 查询 | 端点 | 方法 | 请求体 |
|------|------|------|--------|
| 最新区块 | `/wallet/getnowblock` | POST | `{}` |
| 交易详情 | `/wallet/gettransactionbyid` | POST | `{"value":"64hex_txid"}` |
| 交易费用+区块号 | `/wallet/gettransactioninfobyid` | POST | `{"value":"64hex_txid"}` |

## TRC-20 转账(USDT)解析

method_id `a9059cbb` = `transfer(address,uint256)`

```
data = a9059cbb + 0000...0000(填充) + 接收方地址(20字节) + 金额(32字节大端)
```

步骤：
1. 去掉 `a9059cbb`(4字节)
2. 去掉前12字节填充(`0000...0000`)
3. 剩余20字节 = 接收方hex地址 → 加`41`前缀 → base58
4. 最后32字节 = 金额(大端序)，USDT精度=6

## 地址转换

```python
import hashlib, base58
def hex_to_base58(hex_addr):
    if hex_addr.startswith('0x'): hex_addr = hex_addr[2:]
    addr_bytes = bytes.fromhex(hex_addr)
    h = hashlib.sha256(hashlib.sha256(addr_bytes).digest()).digest()[:4]
    return base58.b58encode(addr_bytes + h).decode()
```

## 常用TRC-20合约

- **USDT**: base58=`TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t`, hex=`41a614f803b6fd780986a42c78ec9c7f77e6ded13c`, 精度=6

## 错误排查

- 空响应 `{}` → txid 不存在或误加了 `0x` 前缀
- 先用 `gettransactionbyid`(最基本)确认交易存在，再用 `gettransactioninfobyid` 拿区块号和费用
