#!/usr/bin/env python3
"""
区块链查询工具 - 统一接口
用法: python3 chain_query.py <chain> <mode> [value]
链: eth, bsc, polygon, arbitrum, btc, sol, tron
模式: tx (交易详情), addr (地址信息), block (最新区块), gas (Gas)
"""

import sys
import json
import urllib.request
import urllib.error

CHAINS = {
    "eth": {"name": "Ethereum", "rpc": "https://eth.drpc.org", "symbol": "ETH", "decimals": 18},
    "bsc": {"name": "BNB Chain", "rpc": "https://bsc.publicnode.com", "symbol": "BNB", "decimals": 18},
    "polygon": {"name": "Polygon", "rpc": "https://polygon-pokt.nodies.app", "symbol": "MATIC", "decimals": 18},
    "arbitrum": {"name": "Arbitrum", "rpc": "https://arb1.arbitrum.io/rpc", "symbol": "ETH", "decimals": 18},
}

def rpc_call(rpc_url, method, params=None):
    data = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}
    req = urllib.request.Request(
        rpc_url,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

def query_evm_tx(chain, tx_hash):
    info = CHAINS[chain]
    tx = rpc_call(info["rpc"], "eth_getTransactionByHash", [tx_hash])
    if "error" in tx:
        print(f"❌ RPC错误: {tx['error']}")
        return
    tx = tx.get("result", {})
    if not tx:
        print("❌ 交易不存在")
        return
    
    receipt = rpc_call(info["rpc"], "eth_getTransactionReceipt", [tx_hash])
    receipt = receipt.get("result", {})
    
    value_eth = int(tx.get("value", "0x0"), 16) / (10 ** info["decimals"])
    gas_price = int(tx.get("gasPrice", "0x0"), 16) / 1e9
    gas_used = int(receipt.get("gasUsed", "0x0"), 16) if receipt else 0
    gas_limit = int(tx.get("gas", "0x0"), 16)
    tx_fee_eth = int(receipt.get("gasUsed", "0x0"), 16) * int(tx.get("gasPrice", "0x0"), 16) / (10 ** info["decimals"]) if receipt else 0
    status = "✅ 成功" if receipt and receipt.get("status") == "0x1" else ("❌ 失败" if receipt else "⏳ 待确认")
    nonce = int(tx.get("nonce", "0x0"), 16)
    
    print(f"""
## 📊 {info['name']} 交易详情

**交易哈希**: `{tx_hash}`
**状态**: {status}
**区块**: #{int(tx.get('blockNumber', '0x0'), 16)}

### 金额信息
- **转账金额**: {value_eth:.6f} {info['symbol']}
- **交易费**: {tx_fee_eth:.8f} {info['symbol']}
- **Gas单价**: {gas_price:.2f} Gwei
- **Gas用量**: {gas_used:,} / {gas_limit:,}

### 参与方
- **From**: `{tx.get('from', 'N/A')}`
- **To**: `{tx.get('to', 'N/A')}`
- **Nonce**: {nonce}

### 事件日志
- **Logs数量**: {len(receipt.get('logs', []))} 条
""")

def query_evm_addr(chain, address):
    info = CHAINS[chain]
    balance = rpc_call(info["rpc"], "eth_getBalance", [address, "latest"])
    nonce = rpc_call(info["rpc"], "eth_getTransactionCount", [address, "latest"])
    
    bal_eth = int(balance.get("result", "0x0"), 16) / (10 ** info["decimals"]) if "result" in balance else 0
    tx_count = int(nonce.get("result", "0x0"), 16) if "result" in nonce else 0
    
    print(f"""
## 📊 {info['name']} 地址信息

**地址**: `{address}`
**余额**: {bal_eth:.6f} {info['symbol']}
**交易总数**: {tx_count} 笔
**最新区块**: #{int(rpc_call(info['rpc'], 'eth_blockNumber').get('result','0x0'),16)}
""")

def query_btc(mode, value=""):
    if mode == "block":
        h = urllib.request.urlopen("https://mempool.space/api/blocks/tip/height", timeout=8).read()
        print(f"## 📊 Bitcoin 最新区块\n\n**高度**: #{h.decode()}")
    elif mode == "gas":
        d = json.loads(urllib.request.urlopen("https://mempool.space/api/v1/fees/recommended", timeout=8).read())
        print(f"""
## 📊 Bitcoin Gas费

| 优先级 | 费率 |
|--------|------|
| 🔴 最快 | {d['fastestFee']} sat/vB |
| 🟡 半小时 | {d['halfHourFee']} sat/vB |
| 🟢 经济 | {d['economyFee']} sat/vB |
""")
    elif mode == "tx":
        d = json.loads(urllib.request.urlopen(f"https://mempool.space/api/tx/{value}", timeout=8).read())
        status = "✅ 确认" if d.get("status", {}).get("confirmed") else "⏳ 未确认"
        val_btc = sum(o.get("value", 0) for o in d.get("vout", [])) / 1e8
        print(f"""
## 📊 Bitcoin 交易详情

**交易ID**: `{value}`
**状态**: {status}
**区块**: #{d.get('status', {}).get('block_height', 'N/A')}
**转账金额**: {val_btc:.8f} BTC
**输入**: {len(d.get('vin', []))} 个UTXO
**输出**: {len(d.get('vout', []))} 个地址
""")
    elif mode == "addr":
        d = json.loads(urllib.request.urlopen(f"https://mempool.space/api/address/{value}", timeout=8).read())
        tx_count = d.get("chain_stats", {}).get("tx_count", 0)
        bal = (d.get("chain_stats", {}).get("funded_txo_sum", 0) - d.get("chain_stats", {}).get("spent_txo_sum", 0)) / 1e8
        print(f"""
## 📊 Bitcoin 地址信息

**地址**: `{value}`
**余额**: {bal:.8f} BTC
**交易总数**: {tx_count} 笔
""")

def query_sol(mode, value=""):
    if mode == "block":
        d = json.loads(urllib.request.urlopen(urllib.request.Request(
            "https://api.mainnet-beta.solana.com", 
            data=json.dumps({"jsonrpc":"2.0","id":1,"method":"getSlot"}).encode(),
            headers={"Content-Type":"application/json"}
        ), timeout=8).read())
        print(f"## 📊 Solana\n\n**最新Slot**: #{d['result']}")
    elif mode == "addr":
        d = json.loads(urllib.request.urlopen(urllib.request.Request(
            "https://api.mainnet-beta.solana.com",
            data=json.dumps({"jsonrpc":"2.0","id":1,"method":"getBalance","params":[value]}).encode(),
            headers={"Content-Type":"application/json"}
        ), timeout=8).read())
        bal = d.get("result", {}).get("value", 0) / 1e9
        print(f"""
## 📊 Solana 地址信息

**地址**: `{value}`
**余额**: {bal:.9f} SOL
""")

def tron_rpc(endpoint, data):
    """通用TRON API调用"""
    import urllib.request
    req = urllib.request.Request(
        f"https://api.trongrid.io{endpoint}",
        data=json.dumps(data).encode() if isinstance(data, dict) else data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    return json.loads(urllib.request.urlopen(req, timeout=10).read())

def hex_to_tron_base58(hex_addr):
    """TRON hex地址转base58"""
    import hashlib, base58
    if hex_addr.startswith('0x'):
        hex_addr = hex_addr[2:]
    addr_bytes = bytes.fromhex(hex_addr)
    h = hashlib.sha256(hashlib.sha256(addr_bytes).digest()).digest()[:4]
    return base58.b58encode(addr_bytes + h).decode()

def query_tron(mode, value=""):
    try:
        if mode == "block":
            d = tron_rpc("/wallet/getnowblock", {})
            bh = d["block_header"]["raw_data"]["number"]
            print(f"## 📊 TRON\n\n**最新区块**: #{bh:,}")
        
        elif mode == "tx":
            d = tron_rpc("/wallet/gettransactionbyid", {"value": value})
            if "Error" in d or "error" in d:
                print(f"❌ TRON交易未找到: {d.get('Error', d.get('error', ''))}")
                return
            
            # 基本信息
            ret_status = d.get("ret", [{}])[0].get("contractRet", "UNKNOWN")
            raw = d.get("raw_data", {})
            contract = raw.get("contract", [{}])[0]
            p = contract.get("parameter", {}).get("value", {})
            contract_type = contract.get("type", "")
            ts = raw.get("timestamp", 0) / 1000
            from datetime import datetime
            time_str = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S UTC')
            
            # 获取费用/区块信息
            info = tron_rpc("/wallet/gettransactioninfobyid", {"value": value})
            block_num = info.get("blockNumber", "N/A")
            fee = info.get("fee", 0)
            energy = info.get("receipt", {}).get("energy_usage", 0)
            
            from_addr = p.get('owner_address', 'N/A')
            data = p.get('data', '')
            
            print(f"""
## 📊 TRON 交易详情

**交易哈希**: `{value}`
**状态**: {'✅ ' + ret_status}
**区块**: #{block_num:,}
**时间**: {time_str}
**类型**: {contract_type}

### 金额信息
- **手续费**: {fee/1e6:.4f} TRX
- **能量消耗**: {energy}

### 参与方
- **发送方**: {from_addr}
""")
            # 如果是TRC-20转账，解码
            if data and len(data) >= 8:
                method_id = data[:8]
                if method_id == 'a9059cbb':
                    to_hex = '41' + data[32:72]
                    amount = int(data[72:], 16)
                    to_b58 = hex_to_tron_base58(to_hex)
                    print(f"""
### 代币转账
- **类型**: TRC-20 转账
- **接收方**: {to_b58}
- **数量(最小单位)**: {amount:,}
- **方法**: transfer (a9059cbb)
""")
        
        elif mode == "addr":
            # TRON账户查询
            d = tron_rpc("/wallet/getaccount", {"address": value if value.startswith('41') else value})
            bal = d.get("balance", 0)
            print(f"""
## 📊 TRON 地址信息

**地址**: `{value}`
**余额**: {bal/1e6:.6f} TRX
""")
    
    except Exception as e:
        print(f"❌ TRON查询失败: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python3 chain_query.py <chain> <mode> [value]")
        print("  链: eth/bsc/polygon/arbitrum/btc/sol/tron")
        print("  模式: tx/addr/gas/block")
        sys.exit(1)
    
    chain = sys.argv[1].lower()
    mode = sys.argv[2].lower()
    value = sys.argv[3] if len(sys.argv) > 3 else ""
    
    if chain == "btc":
        query_btc(mode, value)
    elif chain == "sol":
        query_sol(mode, value)
    elif chain == "tron":
        query_tron(mode, value)
    elif chain in CHAINS:
        if mode == "tx":
            query_evm_tx(chain, value)
        elif mode == "addr":
            query_evm_addr(chain, value)
        elif mode == "gas":
            gas = rpc_call(CHAINS[chain]["rpc"], "eth_gasPrice")
            gwei = int(gas.get("result", "0x0"), 16) / 1e9
            bh = int(rpc_call(CHAINS[chain]["rpc"], "eth_blockNumber").get("result","0x0"),16)
            print(f"## 📊 {CHAINS[chain]['name']} Gas\n\n**区块**: #{bh}\n**Gas价格**: {gwei:.2f} Gwei")
        elif mode == "block":
            bh = int(rpc_call(CHAINS[chain]["rpc"], "eth_blockNumber").get("result","0x0"),16)
            print(f"## 📊 {CHAINS[chain]['name']}\n\n**最新区块**: #{bh}")
    else:
        print(f"❌ 不支持的链: {chain}")
