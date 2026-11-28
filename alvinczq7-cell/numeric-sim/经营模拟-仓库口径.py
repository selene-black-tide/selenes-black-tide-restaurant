# -*- coding: utf-8 -*-
"""
经营数值模拟 v2：按组长 11-28 回复的『仓库口径』重跑

组长回复要点（已定）：
  · 食材上限 = 仓库容量；计划单里的「x/20」作废
  · 仓库容量初期 ≈ 3~5 天用量（约 100），随厨房 / 仓库等级提升
  · 肉鸽每次掉落按「一周 130~220 套」倒推，一次带回百套级
  · 种田按「每日补素菜」的量定
  · 其余参数都可改，参数名不改

本脚本把上面几条放进模型，其它（风评→来客换算、荤 / 素 / 调味的拆分比例、B 菜占比）仍是『假设』。
  python 经营模拟-仓库口径.py --seeds 200
"""
import random
import statistics
import sys

# ---- 文档给定（演示参数）
A = dict(t=30, price=100)
B = dict(t=50, price=300)
KITCHEN = {"W1": 960, "W2": 1680, "W3": 2544}
SEATS = 30
K, S0 = 1.0, 0.9
WAGE = 2000
DEATH_P, DEATH_REP = 0.05, -0.3
SP_REP, SP_CASH, SP_B = 0.15, 1000, 5


def plan(minutes, st, demand):
    """st: dict 肉A 蔬A 肉B 蔬B 调。返回 (收入, a, b)。B 每分钟收入更高，先排 B。"""
    best = (0, 0, 0)
    bmax = int(min(st["肉B"], st["蔬B"], st["调"], minutes // B["t"]))
    for b in range(bmax + 1):
        left = minutes - b * B["t"]
        a = int(min(st["肉A"], st["蔬A"], left // A["t"]))
        sb = min(b, demand)
        sa = min(a, max(0, demand - sb))
        rev = sb * 300 + sa * 100
        if rev > best[0]:
            best = (rev, a, b)
    return best


def guests(rep, mapping):
    r = max(0.0, min(100.0, rep)) / 100
    return SEATS * (r if mapping == "线性" else 0.5 + 0.5 * r)


def run(kitchen, cap, drop, b_share, farm_per_day, rep0, weeks, rng,
        mapping="线性", ration=True, p_special=0, fixed_demand=None):
    """
    cap          每种食材的仓库容量
    drop         肉鸽每周带回的『套数』（肉；调味 = B 的套数）
    b_share      drop 里 B 菜（肉B + 调味）所占比例
    farm_per_day 每天种田补的素菜（每种）
    fixed_demand 给定则每天需求固定（用于不带风评的纯供需账）
    """
    mins = KITCHEN[kitchen]
    st = {"肉A": 0, "蔬A": 0, "肉B": 0, "蔬B": 0, "调": 0}
    rep = rep0
    out = dict(rev=[], made=[], rep=[], waste=[], s=[], stockout=[])
    dB = drop * b_share
    dA = drop - dB
    for w in range(weeks):
        # 第 0 天出肉鸽：补肉和调味，超出仓库容量的白丢
        lost = 0
        for k, v in (("肉A", dA), ("肉B", dB), ("调", dB)):
            nv = st[k] + v
            lost += max(0, nv - cap)
            st[k] = min(cap, nv)
        wrev = made_w = 0
        so = 0
        sw = []
        for d in range(7):
            for k in ("蔬A", "蔬B"):
                st[k] = min(cap, st[k] + farm_per_day)
            dem = fixed_demand if fixed_demand else int(round(guests(rep, mapping) * rng.uniform(2, 3)))
            left = 7 - d
            budget = dict(st)
            if ration:
                for k in ("肉A", "肉B", "调"):
                    budget[k] = -(-st[k] // left)          # 向上取整的『平均每天』
            n_sp = 0
            if p_special:
                for _ in range(p_special):
                    if budget["肉B"] >= SP_B and budget["蔬B"] >= SP_B and budget["调"] >= SP_B and mins >= SP_B * 50:
                        n_sp += 1
                        for k in ("肉B", "蔬B", "调"):
                            budget[k] -= SP_B
            rev, a, b = plan(mins - n_sp * SP_B * 50, budget, max(0, dem - n_sp * SP_B))
            use = {"肉A": a, "蔬A": a, "肉B": b + n_sp * SP_B, "蔬B": b + n_sp * SP_B, "调": b + n_sp * SP_B}
            for k, v in use.items():
                st[k] -= v
            made = a + b + n_sp * SP_B
            served = min(made, dem)
            s = 1.0 if dem == 0 else min(served / dem, 1.0)
            rev += n_sp * (SP_B * 300 + SP_CASH)
            if made == 0 and dem > 0:
                so += 1
            d_rep = K * (s - S0) + n_sp * SP_REP
            if (b + n_sp * SP_B) > 0 and rng.random() < DEATH_P:
                d_rep += DEATH_REP
            rep = max(0.0, min(100.0, rep + d_rep))
            wrev += rev
            made_w += made
            sw.append(s)
        out["rev"].append(wrev - WAGE)
        out["made"].append(made_w)
        out["rep"].append(rep)
        out["waste"].append(lost)
        out["s"].append(statistics.mean(sw))
        out["stockout"].append(so)
    return out


def mc(seeds, **kw):
    rs = [run(rng=random.Random(i), **kw) for i in range(seeds)]
    f = lambda key: [statistics.mean(r[key][w] for r in rs) for w in range(len(rs[0][key]))]
    return {k: f(k) for k in ("rev", "made", "rep", "waste", "s", "stockout")}


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
    wk = 20

    print("## 1. 组长给的组合（仓库 100、一周掉 130~220 套）直接跑：W1，需求固定 75 份/天\n")
    print("B 菜占掉落 40%（假设）；素菜每天补 25 套（假设）。\n")
    rows = []
    for cap in (100, 150, 220):
        for drop in (130, 175, 220):
            o = mc(seeds, kitchen="W1", cap=cap, drop=drop, b_share=0.4, farm_per_day=25, rep0=50,
                   weeks=wk, fixed_demand=75)
            rows.append((cap, drop, f"{statistics.mean(o['made'][2:]):.0f}", f"{statistics.mean(o['waste'][2:]):.0f}",
                         f"{statistics.mean(o['rev'][2:]):.0f}", f"{statistics.mean(o['stockout'][2:]):.1f}"))
    md(rows, ["仓库容量", "每周掉落(套)", "周出品(份)", "每周白丢(套)", "周净收入(￥)", "断货天数/周"])
    print("白丢 = 肉鸽一次带回、仓库装不下的部分（一周只有一次肉鸽，所以容量必须 ≥ 掉落量）。\n")

    print("## 2. 一周掉落 vs 三个厨房阶段（仓库容量 = 掉落量，B 占 40%，素菜足够，需求固定 75）\n")
    rows = []
    for kit in KITCHEN:
        for drop in (130, 175, 220, 300, 400, 500):
            o = mc(seeds // 2, kitchen=kit, cap=drop, drop=drop, b_share=0.4, farm_per_day=drop // 5, rep0=50,
                   weeks=wk, fixed_demand=75)
            made = statistics.mean(o["made"][2:])
            rev = statistics.mean(o["rev"][2:])
            rows.append((kit, drop, f"{made:.0f}", f"{made / (75 * 7):.0%}", f"{rev:.0f}", f"{WAGE / (rev + WAGE):.0%}"))
    md(rows, ["阶段", "每周掉落", "周出品(份)", "占周需求(525)", "周净收入(￥)", "厨师长工资占比"])

    print("## 3. 满足率/风评压力：需求固定 75 份，不同掉落量下的平均满足率\n")
    rows = []
    for drop in (130, 220, 300, 400, 525):
        o = mc(seeds // 2, kitchen="W3", cap=drop, drop=drop, b_share=0.4, farm_per_day=drop // 5, rep0=50,
               weeks=wk, fixed_demand=75)
        s = statistics.mean(o["s"][2:])
        rows.append((drop, f"{s:.2f}", f"{K * (s - S0):+.2f}"))
    md(rows, ["每周掉落(W3 厨房)", "平均满足率 s", "Δ风评/天"])

    print("## 4. 带风评动态（线性假设）：初始风评取多少，才不会开局就崩？W1，仓库 = 掉落 = 175\n")
    rows = []
    for rep0 in (20, 30, 40, 50, 70):
        o = mc(seeds, kitchen="W1", cap=175, drop=175, b_share=0.4, farm_per_day=35, rep0=rep0, weeks=26)
        rows.append((rep0, f"{o['rep'][0]:.1f}", f"{o['rep'][7]:.1f}", f"{o['rep'][25]:.1f}",
                     f"{statistics.mean(o['rev'][:4]):.0f}", f"{statistics.mean(o['rev'][-4:]):.0f}"))
    md(rows, ["初始风评", "第1周末风评", "第8周", "第26周", "前4周周净收入", "末4周周净收入"])

    print("## 5. 配餐：掉落里 B 菜占比（W2，仓库 = 掉落 = 250）\n")
    rows = []
    for bs in (0.2, 0.4, 0.6, 0.8):
        o = mc(seeds // 2, kitchen="W2", cap=250, drop=250, b_share=bs, farm_per_day=50, rep0=50, weeks=wk, fixed_demand=75)
        rows.append((f"{bs:.0%}", f"{statistics.mean(o['made'][2:]):.0f}", f"{statistics.mean(o['rev'][2:]):.0f}"))
    md(rows, ["B 占比", "周出品", "周净收入"])

    print("## 6. 加上特殊单（每天 1 个），W2，仓库 = 掉落 = 250，B 占 40%\n")
    rows = []
    for sp in (0, 1, 2):
        o = mc(seeds // 2, kitchen="W2", cap=250, drop=250, b_share=0.4, farm_per_day=50, rep0=50, weeks=wk, p_special=sp)
        rows.append((sp, f"{statistics.mean(o['rev'][2:]):.0f}", f"{o['rep'][-1]:.1f}", f"{statistics.mean(o['s'][2:]):.2f}"))
    md(rows, ["特殊单/天", "周净收入", f"第{wk}周风评", "平均 s"])


if __name__ == "__main__":
    main()
