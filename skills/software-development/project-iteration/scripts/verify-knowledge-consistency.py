#!/usr/bin/env python3
"""
VisePanda Knowledge Consistency Verifier

Run after expanding food, hotel, transport, or any city-keyed knowledge files.
Checks that all keys across knowledge modules match the CITIES database.

Usage:
    python scripts/verify-knowledge-consistency.py

Exit codes:
    0 — all consistent
    1 — mismatches found
"""

import sys
import os

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.knowledge.cities import CITIES
from data.knowledge.food import FOOD
from data.knowledge.hotels import HOTELS
from data.knowledge.tips import TIPS
from data.knowledge.transport import TRANSPORT as T

all_cities = set(CITIES.keys())
food_keys = set(FOOD.keys())
hotel_keys = set(HOTELS.keys())
tips_keys = set(TIPS.keys())

# Regions in CITIES that are areas, not individual cities
REGIONS = {'yunnan', 'tibet', 'hainan', 'dali', 'macau', 'taipei'}

errors = 0
warnings = 0

def e(msg):
    global errors
    print(f'  ❌ {msg}')
    errors += 1

def w(msg):
    global warnings
    print(f'  ⚠️  {msg}')
    warnings += 1

print('=' * 50)
print('VisePanda 知识库一致性检查')
print('=' * 50)

# 1. CITIES overview
print(f'\n📊 CITIES: {len(all_cities)} entries')
city_list = sorted(all_cities)
print(f'   Keys: {", ".join(city_list)}')

# 2. FOOD check
print(f'\n🍜 FOOD: {len(food_keys)} entries')
for k in sorted(food_keys):
    if k not in all_cities:
        e(f'FOOD 有多余键 "{k}" — 不在 CITIES 中')
        continue
    items = FOOD[k]
    if len(items) < 3:
        w(f'FOOD["{k}"] 仅 {len(items)} 项（建议 ≥5）')
    must_try = sum(1 for i in items if i.get('must_try'))
    if must_try < 2:
        w(f'FOOD["{k}"] 仅 {must_try} 个 must_try（建议 ≥2）')

for k in sorted(city_list):
    if k not in REGIONS and k not in food_keys:
        w(f'CITIES 有 "{k}" 但 FOOD 无对应数据')

# 3. HOTEL check
print(f'\n🏨 HOTELS: {len(hotel_keys)} entries')
for k in sorted(hotel_keys):
    if k not in all_cities:
        e(f'HOTELS 有多余键 "{k}" — 不在 CITIES 中')
        continue

for k in sorted(city_list):
    if k not in hotel_keys:
        w(f'CITIES 有 "{k}" 但 HOTELS 无对应数据')

# 4. TIPS check  
print(f'\n💡 TIPS: {len(tips_keys)} entries')
for k in sorted(tips_keys):
    if k not in all_cities:
        e(f'TIPS 有多余键 "{k}" — 不在 CITIES 中')

# 5. TRANSPORT check
print(f'\n🚄 TRANSPORT: {len(T.get("hsr", []))} HSR routes, {len(T.get("flights", []))} flights')

# Summary
print('\n' + '=' * 50)
if errors == 0 and warnings == 0:
    print(f'✅ 完全一致！无错误，无警告')
    sys.exit(0)
elif errors == 0:
    print(f'✅ 无错误，但有 {warnings} 条警告（建议查看）')
    sys.exit(0)
else:
    print(f'❌ 发现 {errors} 个错误，{warnings} 条警告')
    print('请修复后再提交')
    sys.exit(1)
