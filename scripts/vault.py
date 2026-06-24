#!/usr/bin/env python3
"""
密码本 (Password Vault) — 安全存储和检索凭据。
用法:
  python3 vault.py add <平台名> [--username=...] [--password=...] [--api-key=...] [--api-secret=...] [--notes=...]
  python3 vault.py get <平台名>
  python3 vault.py list
  python3 vault.py delete <平台名>
"""

import json
import os
import sys
from datetime import date

VAULT_PATH = os.path.expanduser("~/.hermes/vault/credentials.json")


def load():
    if not os.path.exists(VAULT_PATH):
        return {}
    with open(VAULT_PATH) as f:
        return json.load(f)


def save(data):
    os.makedirs(os.path.dirname(VAULT_PATH), exist_ok=True)
    with open(VAULT_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.chmod(VAULT_PATH, 0o600)


def mask(value):
    """脱敏显示：只显示前4后4"""
    if not value or len(value) <= 8:
        return value[:2] + "****" if value else ""
    return value[:4] + "****" + value[-4:]


def cmd_add(args):
    data = load()
    name = args[0]

    entry = data.get(name, {})
    entry["created"] = entry.get("created", str(date.today()))
    entry["updated"] = str(date.today())

    # Parse key=value pairs
    for arg in args[1:]:
        if arg.startswith("--"):
            keyval = arg[2:].split("=", 1)
            if len(keyval) == 2:
                key, val = keyval
                entry[key] = val

    data[name] = entry
    save(data)
    print(f"✅ 已保存「{name}」的凭据")


def cmd_get(args):
    data = load()
    name = args[0]
    entry = data.get(name)
    if not entry:
        print(f"❌ 未找到「{name}」的凭据")
        return

    print(f"📋 {name}")
    for key, val in entry.items():
        if key in ("created", "updated"):
            print(f"  {key}: {val}")
        elif key in ("password", "api_key", "api_secret", "secret"):
            print(f"  {key}: {mask(val)}  (完整: {val})")
        else:
            print(f"  {key}: {val}")


def cmd_list(args):
    data = load()
    if not data:
        print("📭 密码本为空")
        return
    print(f"📖 密码本 ({len(data)} 个平台)")
    print("")
    for name in sorted(data.keys()):
        entry = data[name]
        updated = entry.get("updated", "?")
        has_api = "🔑" if entry.get("api_key") else ""
        has_pwd = "🔐" if entry.get("password") else ""
        print(f"  {has_api}{has_pwd} {name}  (更新: {updated})")


def cmd_delete(args):
    data = load()
    name = args[0]
    if name in data:
        del data[name]
        save(data)
        print(f"🗑️ 已删除「{name}」")
    else:
        print(f"❌ 未找到「{name}」")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "add": cmd_add,
        "get": cmd_get,
        "list": cmd_list,
        "delete": cmd_delete,
    }

    fn = commands.get(cmd)
    if not fn:
        print(f"未知命令: {cmd}")
        print(__doc__)
        return

    if cmd in ("get", "delete") and not args:
        print(f"用法: vault.py {cmd} <平台名>")
        return

    if cmd == "add" and not args:
        print(f"用法: vault.py add <平台名> [--key=value ...]")
        return

    fn(args)


if __name__ == "__main__":
    main()
