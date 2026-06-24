#!/usr/bin/env python3
"""Re-runnable verification: 5 scenarios to validate game theory engine decisions."""

import sys
sys.path.insert(0, '.')

from txpokerassist.card import parse_card
from txpokerassist.game_theory import analyze, PlayerAction

SCENARIOS = []

# 1. AA vs tight range → all-in
SCENARIOS.append({
    "name": "AA vs top10 (should all-in)",
    "hero": [parse_card('Ah'), parse_card('Ad')],
    "community": [],
    "pot": 50, "call": 15, "stack": 200,
    "position": 3, "players": 2,
    "actions": [PlayerAction(1, 'raise', 15, 'preflop', 0)],
    "ranges": ['top10'],
    "expect_equity_gt": 0.75,
    "expect_action_in": ["all_in", "raise"],
})

# 2. AhKh flush+straight draw → aggressive
SCENARIOS.append({
    "name": "AhKh on QhJh2c (combo draw → raise)",
    "hero": [parse_card('Ah'), parse_card('Kh')],
    "community": [parse_card('Qh'), parse_card('Jh'), parse_card('2c')],
    "pot": 50, "call": 20, "stack": 200,
    "position": 3, "players": 2,
    "actions": [
        PlayerAction(1, 'raise', 12, 'preflop', 0),
        PlayerAction(1, 'bet', 20, 'flop', 0, 1.5),
    ],
    "expect_equity_gt": 0.50,
    "expect_action_in": ["all_in", "raise", "call"],
    "expect_draw_in_desc": True,
})

# 3. 72o vs tight raise → fold
SCENARIOS.append({
    "name": "72o vs top20 (should fold)",
    "hero": [parse_card('7h'), parse_card('2d')],
    "community": [],
    "pot": 50, "call": 20, "stack": 200,
    "position": 3, "players": 2,
    "actions": [PlayerAction(1, 'raise', 20, 'preflop', 0)],
    "ranges": ['top20'],
    "expect_equity_lt": 0.35,
    "expect_action": "fold",
})

# 4. AK top pair top kicker → all-in
SCENARIOS.append({
    "name": "AK on AQ2 (TPTK → value)",
    "hero": [parse_card('Ah'), parse_card('Kd')],
    "community": [parse_card('Ac'), parse_card('Qh'), parse_card('2d')],
    "pot": 100, "call": 30, "stack": 300,
    "position": 3, "players": 2,
    "actions": [
        PlayerAction(1, 'raise', 15, 'preflop', 0),
        PlayerAction(1, 'bet', 30, 'flop', 0, 2.5),
    ],
    "expect_equity_gt": 0.70,
    "expect_hand_in_desc": ["One Pair", "A"],
})

# 5. Gutshot straight draw → call
SCENARIOS.append({
    "name": "67s on 58T (gutshot → marginal)",
    "hero": [parse_card('6h'), parse_card('7h')],
    "community": [parse_card('5d'), parse_card('8c'), parse_card('Tc')],
    "pot": 100, "call": 30, "stack": 300,
    "position": 3, "players": 2,
    "actions": [
        PlayerAction(1, 'call', 10, 'preflop', 0),
        PlayerAction(1, 'bet', 30, 'flop', 0, 2.0),
    ],
    "expect_equity_lt": 0.55,
    "expect_equity_gt": 0.30,
    "expect_action_in": ["call", "raise", "fold"],
})

# Run all scenarios
passed = 0
failed = 0
for i, s in enumerate(SCENARIOS):
    try:
        r = analyze(
            hero_cards=s["hero"],
            community_cards=s["community"],
            pot=s["pot"],
            to_call=s["call"],
            hero_stack=s["stack"],
            hero_position=s["position"],
            num_players=s["players"],
            actions_history=s["actions"],
            opponent_ranges=s.get("ranges"),
            num_simulations=5000,
        )
        eq = r.raw_equity["equity"]
        act = r.optimal.action
        desc = r.hand_description

        checks = []
        if "expect_equity_gt" in s:
            checks.append(eq > s["expect_equity_gt"])
        if "expect_equity_lt" in s:
            checks.append(eq < s["expect_equity_lt"])
        if "expect_action" in s:
            checks.append(s["expect_action"] in act)
        if "expect_action_in" in s:
            checks.append(any(a in act for a in s["expect_action_in"]))
        if "expect_draw_in_desc" in s and s["expect_draw_in_desc"]:
            checks.append(("听牌" in desc or "draw" in desc.lower()))
        if "expect_hand_in_desc" in s:
            checks.append(all(h in desc for h in s["expect_hand_in_desc"]))

        if all(checks):
            print(f"  ✅ [{i+1}] {s['name']}: Equity={eq:.1%}, Action={act}")
            passed += 1
        else:
            print(f"  ❌ [{i+1}] {s['name']}: Equity={eq:.1%}, Action={act}, Desc={desc}")
            failed += 1
    except Exception as e:
        print(f"  💥 [{i+1}] {s['name']}: ERROR — {e}")
        failed += 1

print(f"\n{'='*40}")
print(f"  {passed} passed, {failed} failed / {len(SCENARIOS)} total")
print(f"{'='*40}")
sys.exit(0 if failed == 0 else 1)
