---
name: blockchain-explorer
description: 多链区块链浏览器。通过地址或交易哈希查询链上信息：余额、交易详情、交易历史、代币持仓、Gas价格、区块信息。
version: 1.0.0
triggers:
  - "区块链/查链/链上/地址/哈希/交易/余额/Gas/区块/合约"
  - "0x开头的地址或哈希查询"
  - "查一下这个地址/哈希"
---

# 区块链浏览器 (Blockchain Explorer)

支持通过 **地址 (address)** 或 **交易哈希 (tx hash)** 查询多链链上信息。

## 支持的链

| 链 | 短名 | RPC/API | 限制 |
|----|------|---------|------|
| Bitcoin | btc | mempool.space API | 无需key |
| Ethereum | eth | eth.drpc.org (eth.drpc.org 备用) | 免费RPC |
| BNB Chain | bsc | bsc.publicnode.com | 免费RPC |
| Polygon | polygon | polygon-pokt.nodies.app | 免费RPC |
| Arbitrum | arbitrum | arb1.arbitrum.io/rpc | 免费RPC |
| Solana | sol | api.mainnet-beta.solana.com | 免费RPC |
| TRON | tron | api.trongrid.io | 免费API |

## 识别链

详细启发式判断逻辑见 `references/chain-identification.md`。速查：

- `0x`开头 + 42字符 = EVM地址
- `0x`开头 + 66字符 = EVM交易哈希
- `1`/`3`/`bc1`开头 → Bitcoin地址
- `T`开头(34字符) → TRON地址
- 44字符base58(非0x) → Solana地址
- 纯64位十六进制 → **优先试TRON**（TRON交易哈希不加0x前缀）

## 查询类型

### 1. 按交易哈希查交易详情 (EVM链)
使用JSON-RPC `eth_getTransactionByHash` + `eth_getTransactionReceipt`

输出：
- 交易状态 (成功/失败)
- 发送方/接收方
- 转账金额 (ETH/BSC/MATIC)
- Gas费用
- 区块号 & 时间戳
- 交易日志 (logs)

### 2. 按地址查余额 + 交易数 (EVM链)
使用JSON-RPC `eth_getBalance` + `eth_getTransactionCount`

### 3. 按区块查
使用JSON-RPC `eth_getBlockByNumber`

### 4. Bitcoin查询
使用mempool.space API:
- `/api/address/{addr}` → 地址信息
- `/api/tx/{txid}` → 交易详情
- `/api/blocks/tip/height` → 最新区块高度
- `/api/v1/fees/recommended` → 推荐Gas费

### 5. Solana查询
使用Solana JSON-RPC

### 6. TRON查询
使用trongrid.io API

## 关键工具函数

### EVM RPC通用查询

```bash
# 查询EVM链交易详情
CHAIN_RPC="https://eth.drpc.org"  # eth: eth.drpc.org / bsc: bsc.publicnode.com / polygon: polygon-pokt.nodies.app
TX_HASH="0x..."

# 获取交易
curl -s -X POST "$CHAIN_RPC" -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_getTransactionByHash\",\"params\":[\"$TX_HASH\"]}"

# 获取交易回执
curl -s -X POST "$CHAIN_RPC" -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_getTransactionReceipt\",\"params\":[\"$TX_HASH\"]}"

# 获取地址余额
curl -s -X POST "$CHAIN_RPC" -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_getBalance\",\"params\":[\"$ADDRESS\",\"latest\"]}"

# 获取Gas价格
curl -s -X POST "$CHAIN_RPC" -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_gasPrice\"}"
```

### Bitcoin查询

```bash
# 地址信息
curl -s "https://mempool.space/api/address/{btc_addr}"

# 交易详情
curl -s "https://mempool.space/api/tx/{txid}"

# 最新区块
curl -s "https://mempool.space/api/blocks/tip/height"
```

### 交易历史查询

对于需要交易历史列表的场景（JSON-RPC不支持），使用**浏览器工具**访问区块链浏览器网站：
- Ethereum: etherscan.io
- BSC: bscscan.com
- Polygon: polygonscan.com
- Solana: solscan.io
- Bitcoin: mempool.space
- TRON: tronscan.org

```python
# 示例：用browser查找交易历史
browser_navigate(url=f"https://etherscan.io/address/{address}")
# 然后提取交易表格
```

## 输出格式

查询结果统一格式化：

```
## 📊 [链名] 查询结果

**查询类型**: 交易详情 / 地址信息 / 区块信息

### 基本信息
- 交易哈希 / 地址: `0x...`
- 状态: ✅ 成功 / ❌ 失败 / ⏳ 待确认
- 区块: #12345678

### 金额信息
- 转账金额: X.XX ETH ($XXX.XX)
- Gas费: 0.00XXX ETH ($X.XX)
- Gas单价: X Gwei

### 交易参与方
- From: `0x...`
- To: `0x...`

### 更多信息
- 时间戳: 2026-05-28 10:00:00 UTC
- 交易序号 (nonce): 123
- Logs: N条事件
```

## TRON特殊处理

TRON的API与EVM不同，需要特别注意：

### 地址格式
- TRON内部用hex地址（以`41`开头，42字符）
- 对外展示用base58地址（以`T`开头，34字符）
- 需要用 base58 库进行转换

```python
import hashlib, base58

def hex_to_base58(hex_addr):
    if hex_addr.startswith('0x'):
        hex_addr = hex_addr[2:]
    addr_bytes = bytes.fromhex(hex_addr)
    h = hashlib.sha256(hashlib.sha256(addr_bytes).digest()).digest()[:4]
    return base58.b58encode(addr_bytes + h).decode()
```

### API端点

| 查询 | 端点 | 方法 | 参数 |
|------|------|------|------|
| 最新区块 | `/wallet/getnowblock` | POST | `{}` |
| 交易详情 | `/wallet/gettransactionbyid` | POST | `{"value":"txid(64hex)"}` |
| 交易费用/区块 | `/wallet/gettransactioninfobyid` | POST | `{"value":"txid"}` |

**注意**：TRON的交易哈希**不加**`0x`前缀，直接传64位hex字符串。

### USDT (TRC-20) 识别
- 主合约: `TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t`
- hex: `41a614f803b6fd780986a42c78ec9c7f77e6ded13c`
- 精度: 6位小数
- 转账方法ID: `a9059cbb` (transfer)

## 快速查询脚本

`scripts/chain_query.py` 提供统一查询接口：

```bash
# 查交易详情
python3 scripts/chain_query.py eth tx "0x..."
python3 scripts/chain_query.py bsc tx "0x..."
python3 scripts/chain_query.py polygon tx "0x..."
python3 scripts/chain_query.py btc tx "txid"

# 查地址信息
python3 scripts/chain_query.py eth addr "0x..."
python3 scripts/chain_query.py btc addr "1..."
python3 scripts/chain_query.py sol addr "...base58..."

# 查Gas/区块
python3 scripts/chain_query.py eth gas
python3 scripts/chain_query.py btc block
python3 scripts/chain_query.py tron block
```

## TRON 交易解析（实战确认）

TRON的交易哈希是64位Hex字符串（不加`0x`前缀），使用TRON Grid API:

```bash
# 获取交易详情 (raw_data含contract/参数)
curl -s -X POST "https://api.trongrid.io/wallet/gettransactionbyid" \
  -H "Content-Type: application/json" \
  -d '{"value":"64位hex哈希值"}'

# 获取交易额外信息(区块/费用/时间戳)
curl -s -X POST "https://api.trongrid.io/wallet/gettransactioninfobyid" \
  -H "Content-Type: application/json" \
  -d '{"value":"64位hex哈希值"}'
```

### TRON 地址格式转换

TRON API返回的地址是Hex格式（以`41`开头），需转Base58（以`T`开头）:

```python
import hashlib, base58
def hex_to_base58(hex_addr):
    """TRON hex地址(42字符) → base58地址(T开头)"""
    addr_bytes = bytes.fromhex(hex_addr)
    h = hashlib.sha256(hashlib.sha256(addr_bytes).digest()).digest()[:4]
    return base58.b58encode(addr_bytes + h).decode()
```

### TRC-20 转账解析

当交易`raw_data.contract[0].parameter.value.data`以`a9059cbb`开头时，是TRC-20代币转账：

| 偏移 | 含义 | 说明 |
|------|------|------|
| `0x00-0x03` (4字节) | method_id | `a9059cbb` = `transfer()` |
| `0x04-0x23` (32字节) | 接收方地址 | 前12字节填充0，后20字节为hex地址(`41`开头) |
| `0x24-0x43` (32字节) | 转账金额 | 大端序uint256，精度取决于代币(USDT=6) |

```python
data = p.get('data', '')
if data.startswith('a9059cbb'):
    to_addr = '41' + data[32:72]  # 提取hex地址
    amount = int(data[72:], 16)   # 最小单位金额
    # USDT精度=6, USDC精度=6
    real_amount = amount / 10**6  
```

### 查询合约对应的代币信息

```python
# 通过tronscan API查代币名/符号/精度
import urllib.request, json
contract_hex = "41a614f803b6fd..."  # hex格式合约地址
url = f"https://apilist.tronscan.org/api/token?contract={contract_hex}"
d = json.loads(urllib.request.urlopen(urllib.request.Request(
    url, headers={'User-Agent': 'Mozilla/5.0'}
)).read())
token = d['data'][0] if d.get('data') else {}
name, symbol, decimals = token.get('name'), token.get('symbol'), token.get('decimal')
```

常用TRC-20合约Base58地址：
- `TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t` = **USDT** (精度6)
- `TEkxiTehnzSmSe2XqrBj4w32RUN966rdz8` = **USDC** (精度6)

## 注意事项

1. 公共RPC有限流，查询间隔建议至少1秒
2. 大额交易或频繁查询建议使用付费RPC
3. 交易历史查询需要通过浏览器访问区块链浏览器网站
4. TRON地址Hex转Base58需要手动计算（见上方代码）
5. 服务器在中国网络下：etherscan(403), 1rpc.io(403)可能被墙，用eth.drpc.org替代
6. 对于ERC-20/TRC-20代币余额，需额外的`eth_call`查询
7. TRON `gettransactioninfobyid` 返回的 `blockTimeStamp` 是UTC时间戳，给用户展示时建议转换为北京时间(UTC+8)
7. TRC-20转账的 data 字段用 `a9059cbb` 方法ID标识 transfer，后面32字节是接收方地址（hex，需加41前缀转base58），再后面是金额（最小单位，USDT精度6）
8. 对于ERC-20/TRC-20代币余额，需额外的`eth_call`查询

## 已知坑

### 代理干扰本地服务
本机设置了 HTTP_PROXY，Python 的 `urllib` 会走代理。以下场景会有问题：
- `rclone authorize` 启动的本地 OAuth 服务器 (localhost:53682) → 浏览器通过代理无法访问
- **解决**：在命令前 `unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY` 或使用 `--noproxy "*"`
- `scripts/chain_query.py` 内置的 RPC 调用走代理通常没问题（代理会转发到外部网络）
