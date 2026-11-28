# -*- coding: utf-8 -*-
"""
肉鸽部分数值模拟 v2（对应 2026-11-29 版 Shadorange/character/角色1/game.py，原文件不改）

用法：  python 肉鸽模拟.py               打印全部结果（Markdown 表格）
        python 肉鸽模拟.py --runs 300
        同时写出 肉鸽掉落分布.json 给 经营模拟.py 用

新版 game.py 相比上一版：怪物生命约 ×1.6（敌1 50 / 敌2 55 / 精英1 92 / Boss 280）、
缠绕与多意图已实现、没有战后回血、层数无上限（7 层一循环）、精英 2（史莱姆）已实现、加入角色 2。
本脚本只测角色 1。机器人只是『凑合会打』的策略，用来看相对关系，不代表玩家上限。

掉落肉量取自 docs/10-design/W1数值清单.md（提案）：弱怪 15 / 三小只 20 / 强怪 25 / 精英 35 / Boss 55。
game.py 目前没有按这张表掉肉，所以肉量由本脚本按『打赢的节点』累加。
"""
import contextlib
import importlib.util
import io
import json
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAME_PATH = os.path.normpath(os.path.join(HERE, "..", "..", "Shadorange", "character", "角色1", "game.py"))
spec = importlib.util.spec_from_file_location("game", GAME_PATH)
game = importlib.util.module_from_spec(spec)
spec.loader.exec_module(game)

MEAT = {"敌怪1": 15, "敌怪2": 15, "敌怪3": 15, "三小只": 20, "强怪": 25, "精英": 35, "大树精": 55}

# ------------------------------------------------------------ 倍率（只用于假设扫描）

_orig_E = game.E
_state = {"hp": 1.0}


def _E(name, hp, intents, kind=None):
    if kind not in ("小只", "中只"):
        hp = max(1, round(hp * _state["hp"]))
    return _orig_E(name, hp, intents, kind)


game.E = _E


# ------------------------------------------------------------ 机器人

ATK_VAL = {"打击": 6, "重击": 20, "双重打击": 10, "盾反": 5, "迅捷打击": 7, "横劈": 7, "全力打击": 17, "多重打击": 0}
BLOCK_VAL = {"防御": 5, "盾反": 5, "招架": 8, "闪避": 6, "重甲": 13}
POWERS = ("越战越勇", "拉伸", "刺伤", "省力")
REWARD_RANK = ["越战越勇", "刺伤", "多重打击", "锻炼", "双重释放", "迅捷打击", "盾反", "疾速", "闪避",
               "全力打击", "横劈", "双重打击", "招架", "拉伸", "省力", "激怒", "重甲", "凝神", "透支"]


def incoming(p, enemies):
    tot = 0

    def one(s, e):
        if s[0] == "multi":
            return sum(one(x, e) for x in s[1])
        if s[0] == "atk":
            return (s[1] + e["strength"]) * s[2] + e["rage"]
        if s[0] == "drain":
            return s[1] + e["strength"]
        return 0

    for e in enemies:
        tot += one(e["intents"][e["i"] % len(e["intents"])], e)
    if p.vuln:
        tot = int(tot * 1.5)
    return tot


def est_dmg(p, c):
    if c == "多重打击":
        return 6 * sum(1 for x in p.hand if game.CARDS[x]["kind"] == "攻击")
    base = ATK_VAL.get(c, 0)
    return base + (p.strength if base else 0)


def make_policy(mode):
    def policy(p, enemies):
        if p.stamina <= 0 or not p.hand:
            return "e"
        hand = p.hand
        if mode == "随机":
            return str(random.randint(1, len(hand))) if random.random() < 0.85 else "e"

        def pick(c):
            return str(hand.index(c) + 1)

        for c in POWERS + ("锻炼",):
            if c in hand and (c not in p.powers):
                return pick(c)
        alive = [e for e in enemies if e["hp"] > 0]
        atk_cards = [c for c in hand if c in ATK_VAL]
        total_atk = sum(est_dmg(p, c) for c in atk_cards)
        tot_hp = sum(e["hp"] + e["block"] for e in alive)
        if "双重释放" in hand and any(c in hand for c in ("重击", "全力打击")):
            return pick("双重释放")
        if "激怒" in hand and atk_cards:
            return pick("激怒")
        if "透支" in hand and atk_cards and total_atk >= 20:
            return pick("透支")
        need = incoming(p, alive) - p.block
        if mode == "稳" and need > 0 and total_atk < tot_hp:
            blocks = [c for c in hand if c in BLOCK_VAL]
            if "凝神" in hand and blocks:
                return pick("凝神")
            if blocks:
                return pick(max(blocks, key=lambda c: BLOCK_VAL[c]))
        if "疾速" in hand and p.stamina > 6 and len(atk_cards) < 2:
            return pick("疾速")
        if atk_cards:
            best = max(atk_cards, key=lambda c: est_dmg(p, c) * (len(alive) if c == "横劈" else 1))
            return pick(best)
        blocks = [c for c in hand if c in BLOCK_VAL]
        if blocks and need > 0:
            return pick(max(blocks, key=lambda c: BLOCK_VAL[c]))
        if "疾速" in hand:
            return pick("疾速")
        return "e"
    return policy


# ------------------------------------------------------------ 一局

_turns = [0]
_orig_start = game.Player.start_turn


def _count(self, enemies=None):
    _turns[0] += 1
    return _orig_start(self, enemies)


game.Player.start_turn = _count


def reward(p, mode):
    pool = [c for c in game.REWARD_POOL if game.CARDS[c].get("owner", 1) == 1]
    random.shuffle(pool)
    picks = pool[:3]
    if mode == "随机":
        p.deck.append(random.choice(picks))
    else:
        p.deck.append(min(picks, key=lambda c: REWARD_RANK.index(c) if c in REWARD_RANK else 99))


def run_once(mode, stamina, seed, max_floors=40):
    random.seed(seed)
    game.RUN_STAMINA = stamina
    pol = make_policy(mode)
    p = game.Player(1)
    floors, meat, cleared, cause = [], 0, 0, "回店(通关上限)"
    i = 0
    while cleared < max_floors:
        _, wave = game.FLOORS[i % game.CYCLE]
        enemies = game.make_enemies(wave)
        hp0, st0, t0 = p.hp, p.stamina, _turns[0]
        res = game.battle(p, enemies, "x", pol)
        done = (not enemies) and p.hp > 0
        floors.append(dict(wave=wave, hp=hp0 - max(0, p.hp), st=st0 - p.stamina, turns=_turns[0] - t0, win=done,
                           hp_after=max(0, p.hp), st_after=p.stamina))
        if p.hp <= 0:
            cause = "生命归零"
            meat_kept = 0                      # game.py：倒了 = 全丢
            return dict(cleared=cleared, cause=cause, meat=0, meat_at_risk=meat, floors=floors, stamina=p.stamina)
        if not done:
            cause = "体力见底"
            break
        cleared += 1
        meat += MEAT[wave]
        reward(p, mode)
        i += 1
        if p.stamina <= 0:
            cause = "体力见底"
            break
    return dict(cleared=cleared, cause=cause, meat=meat, meat_at_risk=meat, floors=floors, stamina=p.stamina)


@contextlib.contextmanager
def quiet():
    with contextlib.redirect_stdout(io.StringIO()):
        yield


def batch(runs, mode="稳", stamina=100, hp=1.0):
    _state["hp"] = hp
    with quiet():
        res = [run_once(mode, stamina, s) for s in range(runs)]
    _state["hp"] = 1.0
    return res


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * (len(xs) - 1) + 0.5))]


def md(rows, head):
    print("| " + " | ".join(head) + " |")
    print("|" + "---|" * len(head))
    for r in rows:
        print("| " + " | ".join(str(x) for x in r) + " |")
    print()


def summ(res):
    cl = [r["cleared"] for r in res]
    meat = [r["meat"] for r in res]
    return dict(layers=statistics.mean(cl), med=statistics.median(cl), meat=statistics.mean(meat),
                risk=statistics.mean(r["meat_at_risk"] for r in res),
                p10=pct(meat, .1), p90=pct(meat, .9), ge154=sum(m >= 154 for m in meat) / len(meat),
                dead=sum(r["cause"] == "生命归零" for r in res) / len(res))


def main():
    runs = 300
    if "--runs" in sys.argv:
        runs = int(sys.argv[sys.argv.index("--runs") + 1])

    print("## A. 起手卡组逐个打（每场 50 血新开，体力不限）\n")
    rows = []
    waves = [("敌怪1", "敌怪1"), ("敌怪2", "敌怪2"), ("敌怪3", "敌怪3"), ("三小只", "三小只"), ("敌怪5", "敌怪5"),
             ("敌怪6", "敌怪6"), ("敌怪7", "敌怪7"), ("精英1", "精英1"), ("精英2(史莱姆)", "精英2"), ("大树精", "大树精")]
    with quiet():
        for label, w in waves:
            r = []
            for s in range(runs):
                random.seed(s)
                game.RUN_STAMINA = 10 ** 6
                p = game.Player(1)
                en = game.make_enemies(w)
                t0 = _turns[0]
                game.battle(p, en, "x", make_policy("稳"))
                r.append((p.hp > 0 and not en, _turns[0] - t0, 50 - max(0, p.hp), 10 ** 6 - p.stamina))
            rows.append((label, f"{sum(x[0] for x in r)/runs:.0%}", f"{statistics.mean(x[1] for x in r):.1f}",
                         f"{statistics.mean(x[2] for x in r):.1f}", f"{statistics.mean(x[3] for x in r):.1f}"))
    md(rows, ["遭遇", "胜率", "平均回合", "平均掉血(50 血)", "平均出牌(=体力)"])

    print("## B. 整局（体力 100，当前 game.py 数值，无回血，层数无上限）\n")
    rows = []
    store = {}
    for mode in ("稳", "随机"):
        res = batch(runs, mode)
        store[mode] = [r["meat"] for r in res]
        s = summ(res)
        boss = [r for r in res if any(f["wave"] == "大树精" for f in r["floors"])]
        kill = [r for r in res if any(f["wave"] == "大树精" and f["win"] for f in r["floors"])]
        causes = {c: sum(1 for r in res if r["cause"] == c) for c in sorted(set(r["cause"] for r in res))}
        rows.append((mode, f"{s['layers']:.1f}", f"{s['med']:.0f}", f"{max(r['cleared'] for r in res)}",
                     f"{len(boss)/runs:.0%}", f"{len(kill)/runs:.0%}", f"{s['meat']:.0f}", f"{s['risk']:.0f}",
                     f"{s['p10']}~{s['p90']}", f"{s['ge154']:.0%}", causes))
    md(rows, ["机器人", "平均层数", "中位", "最远", "摸到 Boss", "打死 Boss", "平均带回肉(倒了全丢)", "平均打到的肉(倒了也算)",
              "肉 10%~90% 分位", "肉 ≥154 的局", "结局"])
    json.dump(store, open(os.path.join(HERE, "肉鸽掉落分布.json"), "w"))

    print("## C. 每层消耗（机器人『稳』，只统计到达该层的局）\n")
    res = batch(runs, "稳")
    rows = []
    for k in range(7):
        got = [r["floors"][k] for r in res if len(r["floors"]) > k]
        if not got:
            continue
        rows.append((game.FLOORS[k][0], len(got), f"{statistics.mean(x['hp'] for x in got):.1f}",
                     f"{statistics.mean(x['st'] for x in got):.1f}", f"{statistics.mean(x['hp_after'] for x in got):.0f}",
                     f"{statistics.mean(x['st_after'] for x in got):.0f}", f"{sum(x['win'] for x in got)/len(got):.0%}"))
    md(rows, ["层", "到达局数", "平均掉血", "平均耗体力", "打完后剩血", "打完后剩体力", "该层打赢率"])

    print("## D. 整局体力扫描（当前怪物，机器人『稳』）\n")
    rows = []
    for st in (60, 80, 100, 120, 150, 200, 300):
        s = summ(batch(runs, "稳", stamina=st))
        rows.append((st, f"{s['layers']:.1f}", f"{s['meat']:.0f}", f"{s['ge154']:.0%}", f"{s['dead']:.0%}"))
    md(rows, ["整局体力", "平均层数", "平均带回肉", "肉 ≥154 的局", "生命归零占比"])

    print("## E. 怪物生命倍率 × 整局体力（相对当前 game.py；格子 = 平均层数 / 肉 ≥154 的局占比 / 平均肉）\n")
    rows = []
    for hm in (0.5, 0.6, 0.7, 0.8, 1.0):
        row = [f"×{hm}"]
        for st in (80, 100, 150):
            s = summ(batch(runs, "稳", stamina=st, hp=hm))
            row.append(f"{s['layers']:.1f} / {s['ge154']:.0%} / {s['meat']:.0f}")
        rows.append(row)
    md(rows, ["怪物生命", "体力 80", "体力 100", "体力 150"])

    print("## F. 同一网格，『随机出牌』机器人（新手下限）\n")
    rows = []
    for hm in (0.5, 0.7, 1.0):
        row = [f"×{hm}"]
        for st in (100, 150):
            s = summ(batch(runs, "随机", stamina=st, hp=hm))
            row.append(f"{s['layers']:.1f} / {s['ge154']:.0%} / {s['meat']:.0f}")
        rows.append(row)
    md(rows, ["怪物生命", "体力 100", "体力 150"])

    print("## G. 调参后的掉落分布（供经营模拟使用）：怪物生命 ×0.7、体力 100\n")
    tuned = {}
    for mode in ("稳", "随机"):
        res = batch(runs, mode, stamina=100, hp=0.7)
        tuned[mode] = [r["meat"] for r in res]
    json.dump(tuned, open(os.path.join(HERE, "肉鸽掉落分布-调参.json"), "w"))
    rows = [(m, f"{statistics.mean(v):.0f}", f"{pct(v, .1)}~{pct(v, .9)}", f"{sum(x >= 154 for x in v)/len(v):.0%}")
            for m, v in tuned.items()]
    md(rows, ["机器人", "平均带回肉", "10%~90% 分位", "肉 ≥154 的局"])


if __name__ == "__main__":
    main()
