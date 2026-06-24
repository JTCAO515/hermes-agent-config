# 地址/哈希链识别启发式

> 根据哈希或地址的格式快速判断可能的链。
> 来源：2026-05-28 实战会话，从服务器（中国网络）可用的RPC

## 地址/哈希格式速查

| 格式 | 长度 | 可能链 | 示例 |
|------|------|--------|------|
| `0x`开头 | 42 (0x+40) | EVM地址(ETH/BSC/Polygon/Arbitrum等) | `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045` |
| `0x`开头 | 66 (0x+64) | EVM交易哈希 | `0x4e5a4c6a1f3b2d8c9e0f7a6b5c4d3e2f1a0b9c...` |
| `1`开头 | 26-35 | Bitcoin地址(P2PKH) | `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa` |
| `bc1`开头 | 42-62 | Bitcoin地址(bech32) | `bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq` |
| `3`开头 | 26-35 | Bitcoin地址(P2SH) | `3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy` |
| `T`开头 | 34 | TRON地址(base58) | `TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t` |
| base58(非`0x`) | 44 | Solana地址 | `7EcDhSYGxXyscszYEp35KHN8vvw3svAuLKTzXwCFLtVh` |
| 纯64位十六进制(无前缀) | 64 | TRON交易哈希 **或** Solana交易(base58) | `60f5e0e44e9d5e446606db8b0c53025be5e23302ac9688c83715794459c826eb` |

## 识别策略（按优先级）

### 有`0x`前缀 → EVM链
1. 先试 **Ethereum** (eth.drpc.org) — 最通用
2. 未找到再试 **BSC** (bsc.publicnode.com) — 第二大链
3. 再试 **Polygon** (polygon-pokt.nodies.app)
4. 再试 **Arbitrum** (arb1.arbitrum.io/rpc)

### 无前缀、64位十六进制 → 可能是TRON
1. TRON交易哈希不加`0x`前缀
2. 直接用 `POST /wallet/gettransactionbyid` 查
3. 如果查不到，可能是Solana交易（但Solana也用base58编码，可能性小）

### `T`开头 → TRON地址
1. 用 `POST /v1/accounts/{address}` 查账户信息

### `1`/`3`/`bc1`开头 → Bitcoin
1. 用 mempool.space API

### 44字符base58 → Solana
1. 用 Solana JSON-RPC

## 从中国网络实测可用的端点

| 链 | 端点 | 用途 |
|----|------|------|
| Ethereum | `https://eth.drpc.org` | JSON-RPC (区块/交易/Gas) |
| BSC | `https://bsc.publicnode.com` | JSON-RPC |
| Polygon | `https://polygon-pokt.nodies.app` | JSON-RPC |
| Arbitrum | `https://arb1.arbitrum.io/rpc` | JSON-RPC |
| Bitcoin | `https://mempool.space/api/...` | REST API |
| Solana | `https://api.mainnet-beta.solana.com` | JSON-RPC |
| TRON | `https://api.trongrid.io` | REST API |
| TRON (备用) | `https://api.tronstack.io` | REST API |

## 已屏蔽的站点（中国网络不可用）

| 站点 | 现象 | 替代方案 |
|------|------|----------|
| etherscan.io | 403 / 超时 | 直连RPC查(on-chain数据) |
| bscscan.com | Cloudflare拦截 | 直连RPC查 |
| api.etherscan.io | 超时 | JSON-RPC + 节点 |
| appleid.apple.com | 403 | 无法做iCloud OAuth |
