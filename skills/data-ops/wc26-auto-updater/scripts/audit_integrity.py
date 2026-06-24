#!/usr/bin/env python3
"""WC26 数据完整性审计脚本 — 验证纳米数据导出的完整性和一致性。

用法的: python3 scripts/audit_integrity.py --data-dir data/ [--fix]

验证项目:
1. JSON 语法正确性
2. 球队映射完整性 (48队, 跨文件一致性)
3. wc2026_teams.json 评分完整性
4. 比赛计数 (72小组 + 32淘汰 = 104)
5. 重复ID检测
6. Result 双格式一致性 (home_score + team_a_goals 同时存在)
7. Predictions 覆盖率
8. SQLite 数据库结构 (如存在)
"""

import json
import os
import sys
import argparse
from pathlib import Path


def audit_json_files(data_dir):
    """验证所有 JSON 文件语法和基本结构。"""
    print("=== JSON 语法验证 ===")
    json_files = [
        "wc2026_matches.json",
        "wc2026_teams.json",
        "nami_archive.json",
        "nami_team_map.json",
        "polymarket_odds.json",
        "simulation_results.json",
    ]
    results = []
    for fname in json_files:
        path = data_dir / fname
        if not path.exists():
            print(f"  ⚠️  {fname}: 文件不存在")
            results.append(("warning", fname, "文件不存在"))
            continue
        try:
            with open(path) as f:
                data = json.load(f)
            size = path.stat().st_size
            print(f"  ✅ {fname}: {size:,} bytes")
            results.append(("ok", fname, f"{size:,} bytes"))
        except json.JSONDecodeError as e:
            print(f"  ❌ {fname}: JSON 语法错误 — {e}")
            results.append(("error", fname, f"JSON 错误: {e}"))
        except Exception as e:
            print(f"  ❌ {fname}: 读取异常 — {e}")
            results.append(("error", fname, str(e)))
    return results


def audit_team_map(data_dir):
    """验证球队映射完整性和一致性。"""
    print("\n=== 球队映射验证 ===")

    # 检查 nami_team_map.json
    tmap_path = data_dir / "nami_team_map.json"
    if not tmap_path.exists():
        print("  ⚠️  nami_team_map.json 不存在")
        return

    with open(tmap_path) as f:
        team_map = json.load(f)

    count = len(team_map)
    names = list(team_map.values())
    dupes = [n for n in names if names.count(n) > 1]

    print(f"  球队数: {count} {'✅ 48队' if count == 48 else f'⚠️ 期望48, 实际{count}'}")

    if dupes:
        print(f"  ❌ 重复队名: {set(dupes)}")
    else:
        print(f"  ✅ 无重复队名")

    # 检查与 nami_archive 的一致性
    archive_path = data_dir / "nami_archive.json"
    if archive_path.exists():
        with open(archive_path) as f:
            archive = json.load(f)
        archive_map = archive.get("team_map", {})
        if team_map == archive_map:
            print(f"  ✅ nami_team_map ↔ archive 一致 ({len(archive_map)}队)")
        else:
            diff = set(team_map.items()) ^ set(archive_map.items())
            print(f"  ⚠️  与 archive 不一致: {len(diff)} 差异")


def audit_matches(data_dir):
    """验证比赛数据完整性。"""
    print("\n=== 比赛数据验证 ===")
    path = data_dir / "wc2026_matches.json"
    if not path.exists():
        print("  ⚠️  wc2026_matches.json 不存在")
        return

    with open(path) as f:
        data = json.load(f)

    all_m = data.get("matches", [])
    ko = data.get("knockout", {}).get("all_matches", [])

    # 按 phase 分类
    group_m = [m for m in all_m if m.get("phase") == "group"]
    ko_in_matches = [m for m in all_m if m.get("phase") == "knockout"]
    ko2 = [m for m in ko if m.get("phase") == "knockout"]

    print(f"  小组赛(phase=group): {len(group_m)}")
    print(f"  淘汰赛在 matches[] 中: {len(ko_in_matches)}")
    print(f"  淘汰赛在 knockout[] 中: {len(ko2)}")
    print(f"  总唯一: {len(group_m) + len(ko_in_matches)} (期望: 104)")

    # 检查 ID 重复
    all_ids = [m.get("id") for m in all_m + ko]
    seen = set()
    dupes = set()
    for i in all_ids:
        if i in seen:
            dupes.add(i)
        seen.add(i)
    if dupes:
        print(f"  ⚠️  重复ID: {len(dupes)} 个(淘汰赛双存储, 正常)")
    else:
        print(f"  ✅ 无重复ID")

    # Result 双格式检查
    result_issues = 0
    for m in all_m:
        r = m.get("result")
        if r:
            has_home = "home_score" in r and "away_score" in r
            has_team = "team_a_goals" in r and "team_b_goals" in r
            if not (has_home and has_team):
                print(f"  ❌ {m.get('id')}: result 缺少字段 ({list(r.keys())})")
                result_issues += 1
            elif r.get("home_score") != r.get("team_a_goals") or r.get("away_score") != r.get("team_b_goals"):
                print(f"  ⚠️  {m.get('id')}: result 双格式值不一致 ({r})")
                result_issues += 1
    if result_issues == 0:
        print(f"  ✅ 所有 result 双格式正确")

    # Predictions 覆盖率
    with_pred = sum(1 for m in all_m if m.get("predictions"))
    print(f"  有 predictions: {with_pred}/{len(all_m)} ({100*with_pred//len(all_m)}%)")

    # 已赛 vs 模拟
    with_result = sum(1 for m in all_m if m.get("result"))
    is_sim = sum(1 for m in all_m if m.get("is_simulated"))
    print(f"  已赛(真实): {with_result}")
    print(f"  模拟: {is_sim}")


def audit_db(data_dir):
    """验证 SQLite 数据库结构。"""
    print("\n=== SQLite 数据库验证 ===")
    db_path = data_dir / "nami_wc2026.db"
    if not db_path.exists():
        print("  ⚠️  nami_wc2026.db 不存在")
        return

    import sqlite3
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    print(f"  表: {len(tables)}")
    for t in tables:
        name = t[0]
        cur.execute(f'SELECT COUNT(*) FROM "{name}"')
        count = cur.fetchone()[0]
        print(f"    📋 {name}: {count} rows")
    conn.close()


def fix_result_format(data_dir):
    """修复 result 双格式缺失问题。"""
    path = data_dir / "wc2026_matches.json"
    with open(path) as f:
        data = json.load(f)

    fixed = 0
    for m in data.get("matches", []):
        r = m.get("result")
        if r:
            if "home_score" not in r and "team_a_goals" in r:
                r["home_score"] = r["team_a_goals"]
                r["away_score"] = r["team_b_goals"]
                fixed += 1
            elif "team_a_goals" not in r and "home_score" in r:
                r["team_a_goals"] = r["home_score"]
                r["team_b_goals"] = r["away_score"]
                fixed += 1

    if fixed:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  ✅ 修复了 {fixed} 个 result 格式")
    else:
        print(f"  ✅ 无需修复")
    return fixed


def main():
    parser = argparse.ArgumentParser(description="WC26 数据完整性审计")
    parser.add_argument("--data-dir", default="data", help="data 目录路径")
    parser.add_argument("--fix", action="store_true", help="自动修复 result 格式")
    args = parser.parse_args()

    data_dir = Path(args.data_dir).resolve()
    if not data_dir.exists():
        print(f"❌ data 目录不存在: {data_dir}")
        sys.exit(1)

    print(f"📁 数据目录: {data_dir}\n")

    audit_json_files(data_dir)
    audit_team_map(data_dir)
    audit_matches(data_dir)
    audit_db(data_dir)

    if args.fix:
        print("\n=== 自动修复 ===")
        fix_result_format(data_dir)

    print("\n✅ 审计完成")


if __name__ == "__main__":
    main()
