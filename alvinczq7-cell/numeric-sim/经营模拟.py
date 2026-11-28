# -*- coding: utf-8 -*-
"""
经营部分数值模拟 v2：按 docs/10-design/W1数值清单.md 与 系统-经营供给.md（2026-11-29 版）

数据（均为组长的演示参数 / 提案）：
  风评 30 起；来客 = 座位 × 风评 ÷ 100；每人点 2~3 道；k = 1.5、s0 = 0.9
  座位 30；桌子升级 10000￥（→ 40 座，按 4 座/桌）；二楼 100000￥（+10 桌，按 4 座/桌，我的假设）
  厨房 W1：960min；成品菜 A 30min 100￥，配方 肉 1 + 蔬菜 A 1
  菜园：开局蔬菜 A150 / B100 / C50，A 一周一熟（每周补种 150，清单口径）
  地窖：肉 500 / 菜 500；厨师长 2000￥/周；初始资金 3000￥
  肉：肉鸽周初一局，肉量取自『肉鸽模拟.py』按节点累计（弱怪 15 / 三小只 20 / 强怪 25 / 精英 35 / Boss 55）
我自己加的假设（文档没写，已在报告里标注）：
  · 所有肉都是怪物肉，午夜班每天掷一次暴毙 5% × −0.3
  · 玩家按『预计需求』备菜，不会故意多做
  · 灶台 / 其他雇员价格没有，W2 厨房用参数 kitchen_up_week 控制
用法：python 经营模拟.py --seeds 200
"""
import json
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
K, S0 = 1.5, 0.9
PRICE, T_DISH = 100, 30
WAGE = 2000


def load(name):
    p = os.path.join(HERE, name)
    return json.load(open(p)) if os.path.exists(p) else {}


def run(weeks, rng, meat_src, rep0=30, seats0=30, veg_weekly=150, cash0=3000, kitchen_up_week=None,
        extra_wage=3000, fixed_ratio=None, buy=True, meat_cap=500, veg_cap=500):
    """meat_src: 数字（每周固定）或列表（每周抽一个）"""
    rep, seats, cash = rep0, seats0, cash0
    meat, vega = 0, 150
    kit = 960
    tables_bought = floor_bought = None
    out = []
    for w in range(weeks):
        if kitchen_up_week is not None and w == kitchen_up_week:
            kit = 1680
        extra = extra_wage if kit > 960 else 0
        drop = meat_src if isinstance(meat_src, (int, float)) else (rng.choice(meat_src) if meat_src else 0)
        meat = min(meat_cap, meat + drop)
        if w > 0:
            vega = min(veg_cap, vega + veg_weekly)
        rev = short_days = 0
        dem_total = made_total = 0
        for d in range(7):
            guests = seats * rep / 100
            ratio = fixed_ratio if fixed_ratio else rng.uniform(2, 3)
            dem = int(guests * ratio)
            exp = int(guests * 2.5)
            cap_t = kit // T_DISH
            make = min(exp, cap_t, meat, vega)
            if make < exp and make < cap_t:
                short_days += 1
            meat -= make
            vega -= make
            served = min(make, dem)
            s = 1.0 if dem == 0 else served / dem
            rev += served * PRICE
            d_rep = K * (s - S0)
            if make > 0 and rng.random() < 0.05:
                d_rep -= 0.3
            rep = max(0.0, min(100.0, rep + d_rep))
            dem_total += dem
            made_total += make
        cash += rev - WAGE - extra
        if buy:
            if seats == seats0 and cash >= 10000 + WAGE:
                cash -= 10000
                seats = 40
                tables_bought = w + 1
            elif seats == 40 and cash >= 100000 + WAGE:
                cash -= 100000
                seats = 80
                floor_bought = w + 1
        out.append(dict(rep=rep, seats=seats, rev=rev - WAGE - extra, cash=cash, dem=dem_total / 7,
                        made=made_total / 7, short=short_days, drop=drop, meat=meat))
    return out, tables_bought, floor_bought


def mc(seeds, **kw):
    rs, tb, fb = [], [], []
    for i in range(seeds):
        o, t, f = run(rng=random.Random(i), **kw)
        rs.append(o)
        tb.append(t)
        fb.append(f)
    weeks = len(rs[0])
    agg = {k: [statistics.mean(r[w][k] for r in rs) for w in range(weeks)] for k in rs[0][0]}
    def med(x):
        v = [a for a in x if a]
        return (f"第{statistics.median(v):.0f}周" if len(v) > len(x) / 2 else "未到") if v else "未到"
    return agg, med(tb), med(fb)


def md(rows, head):
    print("| " + " | ".join(head) + " |")
    print("|" + "---|" * len(head))
    for r in rows:
        print("| " + " | ".join(str(x) for x in r) + " |")
    print()


def main():
    seeds = 200
    if "--seeds" in sys.argv:
        seeds = int(sys.argv[sys.argv.index("--seeds") + 1])
    dist = load("肉鸽掉落分布.json")
    tuned = load("肉鸽掉落分布-调参.json")

    print("## 1. 清单口径复算：W1 第一周逐日（来客 9、需求 22、肉 170、蔬菜 A 150）\n")
    meat, vega, rep, rows, rev = 170, 150, 30.0, [], 0
    for d in range(1, 8):
        dem = int(30 * rep / 100 * 2.5)
        make = min(dem, 960 // 30, meat, vega)
        meat -= make
        vega -= make
        s = make / dem
        rep += K * (s - S0)
        rev += make * PRICE
        rows.append((d, dem, make, f"{s:.2f}", f"{K*(s-S0):+.2f}", f"{rep:.2f}", meat, vega))
    md(rows, ["天", "需求", "做", "满足率", "Δ风评", "风评", "剩肉", "剩蔬菜A"])
    print(f"一周收入 {rev}￥、周净利 {rev-WAGE}￥（清单写 15400 / 13400）。\n"
          "清单口径把 300 蔬菜（A150/B100/C50）当成通用菜；成品菜 A 只吃蔬菜 A，开局只有 150。\n")

    print("## 2. 肉需求：随座位与风评一周要多少肉\n")
    rows = []
    for seats in (30, 40, 80):
        row = [seats]
        for rep in (30, 40, 50, 70, 100):
            d = int(seats * rep / 100 * 2.5)
            row.append(f"{d}/天 · {d*7}/周" + ("（超产能）" if d > 32 else ""))
        rows.append(row)
    md(rows, ["座位", "风评30", "风评40", "风评50", "风评70", "风评100"])
    print("W1 厨房一天最多做 32 份（960÷30）。\n")

    print("## 3. 肉鸽带回的肉 vs 需求：20 周模拟（座位按钱升级，W1 厨房，蔬菜 A 每周补 150）\n")
    scen = [("肉鸽每周固定 170（清单口径）", 170)]
    if dist.get("稳"):
        scen.append(("机器人『稳』的真实分布（当前 game.py，倒了全丢）", dist["稳"]))
    if tuned.get("稳"):
        scen.append(("机器人『稳』，怪物生命 ×0.7", tuned["稳"]))
    scen.append(("肉鸽周周空手（对照）", 0))
    rows = []
    for name, src in scen:
        a, tb, fb = mc(seeds, weeks=20, meat_src=src)
        for w in (0, 3, 7, 11, 19):
            rows.append((name if w == 0 else "", f"第{w+1}周", f"{a['rep'][w]:.1f}", f"{a['seats'][w]:.0f}",
                         f"{a['dem'][w]:.1f}", f"{a['made'][w]:.1f}", f"{a['short'][w]:.1f}",
                         f"{a['rev'][w]:.0f}", f"{a['cash'][w]:.0f}"))
        rows.append(("", f"桌子 {tb}；二楼 {fb}", "", "", "", "", "", "", ""))
    md(rows, ["肉鸽供给", "周", "风评", "座位", "日需求", "日出品", "断粮天数/周", "周净收入", "现金"])

    print("## 4. 蔬菜 A 是否够：菜园每周补多少（肉固定 170）\n")
    rows = []
    for vw in (0, 150, 250, 300):
        a, tb, fb = mc(seeds // 2, weeks=12, meat_src=170, veg_weekly=vw)
        rows.append((vw, f"{a['short'][0]:.1f}", f"{a['short'][3]:.1f}", f"{a['short'][11]:.1f}", f"{a['rev'][11]:.0f}"))
    md(rows, ["菜园每周补蔬菜A", "第1周断粮天", "第4周", "第12周", "第12周周净收入"])

    print("## 5. 风评节奏：什么时候撞上 W1 厨房上限（32 份/天）\n")
    rows = []
    for seats in (30, 40):
        a, tb, fb = mc(seeds // 2, weeks=52, meat_src=400, veg_weekly=300, buy=False, seats0=seats, meat_cap=1000, veg_cap=1000)
        hit = next((w + 1 for w in range(52) if a["dem"][w] >= 32), None)
        rows.append((seats, f"{a['rep'][12]:.1f}", f"{a['rep'][25]:.1f}", f"{a['rep'][51]:.1f}",
                     f"{hit}" if hit else "52 周内没有", f"{a['made'][51]:.1f}"))
    md(rows, ["座位", "第13周风评", "第26周", "第52周", "需求触到32份的周", "第52周日出品"])

    print("## 6. W2 厨房（1680min）什么时候值（肉固定 400/周、蔬菜 A 每周 300；额外工资 3000/周 为假设）\n")
    rows = []
    for up in (None, 4, 8):
        a, tb, fb = mc(seeds // 2, weeks=20, meat_src=400, veg_weekly=300, kitchen_up_week=up, meat_cap=800, veg_cap=800)
        rows.append(("不升级" if up is None else f"第{up+1}周升级", f"{statistics.mean(a['rev'][12:20]):.0f}",
                     f"{a['rep'][19]:.1f}", f"{a['made'][19]:.1f}", f"{a['dem'][19]:.1f}"))
    md(rows, ["厨房", "第13~20周均周净收入", "第20周风评", "第20周日出品", "日需求"])


if __name__ == "__main__":
    main()
