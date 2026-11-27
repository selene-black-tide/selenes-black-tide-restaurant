# -*- coding: utf-8 -*-
"""
经营部分数值模拟（只读企划书，不改任何设定）

用法：  python 经营模拟.py            打印全部结果（Markdown 表格）
        python 经营模拟.py --seeds 500

数据来源（全部是组长 11-28 的「演示参数」，不是平衡值）：
  产能   做菜总时长 = Σ(加成 × 工时) × 60     W1=960 / W2=1680 / W3=2544 min
  菜谱   菜A 30min 100￥ (肉A1+蔬菜A1)；菜B 50min 300￥ (肉B1+蔬菜B1+调味A1)
  库存   肉A/蔬菜A/肉B/蔬菜B 上限 20，调味A 上限 10（计划单示例里的 x/20、x/10）
  需求   来客数 × (2~3)，来客数上限 = 座位数 = 30
  风评   Δ = 1.0×(s−0.9)；特殊菜 +0.15 / 个，每天最多 2 个；暴毙 5% × −0.3（午夜班掷一次）
  特殊单 5 份菜B → +1000￥
  工资   厨师长 2000￥/周
  升级   桌子 10000￥；二楼 100000￥

文档里【没有】的东西，下面标「假设」，只为了让模拟能转起来，不是设定：
  · 风评初始值、风评→来客数的换算
  · 肉鸽每周给多少食材
  · 特殊单一天出几个
"""
import itertools
import random
import statistics
import sys

# ------------------------------------------------------------ 文档给定

DISHES = {
    "A": dict(t=30, price=100, need={"肉A": 1, "蔬菜A": 1}),
    "B": dict(t=50, price=300, need={"肉B": 1, "蔬菜B": 1, "调味A": 1}),
}
CAP = {"肉A": 20, "蔬菜A": 20, "肉B": 20, "蔬菜B": 20, "调味A": 10}   # 计划单示例的 x/20、x/10
KITCHEN = {"W1": 960, "W2": 1680, "W3": 2544}                          # min/天
SEATS = 30
ORDER_PER_GUEST = (2, 3)
K, S0 = 1.0, 0.9
SPECIAL_REP, SPECIAL_CASH, SPECIAL_B = 0.15, 1000, 5
DEATH_P, DEATH_REP = 0.05, -0.3
CHEF_WAGE_WEEK = 2000


# ------------------------------------------------------------ 工具

def best_plan(minutes, stock, demand):
    """在时间 / 库存 / 需求三个上限内，枚举 (a,b) 找收入最高的做法。"""
    best = (0, 0, 0)
    bmax = min(stock["肉B"], stock["蔬菜B"], stock["调味A"], minutes // DISHES["B"]["t"])
    for b in range(int(bmax) + 1):
        left = minutes - b * DISHES["B"]["t"]
        amax = min(stock["肉A"], stock["蔬菜A"], left // DISHES["A"]["t"])
        for a in (int(amax),):          # A 单价/分钟低于 B，剩余时间全给 A 即可
            served_b = min(b, demand)
            served_a = min(a, max(0, demand - served_b))
            rev = served_b * 300 + served_a * 100
            if rev > best[0]:
                best = (rev, a, b)
    return best


def full_stock():
    return dict(CAP)


# ------------------------------------------------------------ 一、静态天花板

def static_table():
    rows = []
    for name, mins in KITCHEN.items():
        rev, a, b = best_plan(mins, full_stock(), 10**9)
        used = a * 30 + b * 50
        rows.append((name, mins, a, b, a + b, rev, used, mins - used))
    return rows


def time_only_table():
    """如果食材不设限，纯看时间，W1~W3 能做多少份（全做 A / 全做 B）。"""
    return [(n, m, m // 30, m // 50) for n, m in KITCHEN.items()]


# ------------------------------------------------------------ 二、日循环（含风评）

def guests_from_rep(rep, mapping, seats=SEATS):
    """假设：风评→来客数。文档只说「风评越大来客越多」，没给公式。"""
    r = max(0.0, min(100.0, rep)) / 100
    if mapping == "线性":                 # 来客 = 座位 × 风评/100
        return seats * r
    if mapping == "半线性":               # 来客 = 座位 × (0.5 + 0.5×风评/100)
        return seats * (0.5 + 0.5 * r)
    raise ValueError(mapping)


def run(kitchen, rep0, mapping, weeks, daily_refill, weekly_supply, p_special,
        wage_extra_week, rng, special_enabled=True, seats=SEATS):
    """
    kitchen         W1/W2/W3
    daily_refill    True：库存每天回满（库存上限 = 每天可用量）
                    False：库存是仓库，每周由肉鸽补 weekly_supply 个/种，封顶到 CAP
    weekly_supply   仓库模式下每周每种食材补多少（假设）
    p_special       每天出特殊单的个数（0/1/2，假设）
    """
    rep = rep0
    stock = full_stock() if daily_refill else {k: 0 for k in CAP}
    out = dict(rev=[], rep=[], s=[], waste=[])
    mins = KITCHEN[kitchen]
    for w in range(weeks):
        if not daily_refill:
            for k in stock:
                stock[k] = min(CAP[k], stock[k] + weekly_supply)
        wrev = 0.0
        for d in range(7):
            if daily_refill:
                stock = full_stock()
            guests = guests_from_rep(rep, mapping, seats)
            guests = max(0.0, guests)
            demand = int(round(guests * rng.uniform(*ORDER_PER_GUEST)))
            # 特殊单：需要 5 份 B，先留出来
            n_sp = 0
            if special_enabled and p_special:
                for _ in range(p_special):
                    if stock["肉B"] >= SPECIAL_B and stock["蔬菜B"] >= SPECIAL_B and stock["调味A"] >= SPECIAL_B \
                       and mins >= SPECIAL_B * 50:
                        n_sp += 1
                        stock["肉B"] -= SPECIAL_B; stock["蔬菜B"] -= SPECIAL_B; stock["调味A"] -= SPECIAL_B
            sp_time = n_sp * SPECIAL_B * 50
            sp_dishes = n_sp * SPECIAL_B
            rev, a, b = best_plan(mins - sp_time, stock, max(0, demand - sp_dishes))
            for k, v in (("肉A", a), ("蔬菜A", a), ("肉B", b), ("蔬菜B", b), ("调味A", b)):
                stock[k] -= v
            made = a + b + sp_dishes
            served = min(made, demand)
            s = 1.0 if demand == 0 else min(served / demand, 1.0)
            rev += n_sp * (SPECIAL_B * 300 + SPECIAL_CASH)
            drev = rev
            d_rep = K * (s - S0) + n_sp * SPECIAL_REP
            # 暴毙：菜单含怪物肉类菜品。文档没说哪道菜是怪物肉，这里假设：只要卖出 B 就算
            if (b + sp_dishes) > 0 and served > 0 and rng.random() < DEATH_P:
                d_rep += DEATH_REP
            rep = max(0.0, min(100.0, rep + d_rep))
            wrev += drev
            out["s"].append(s)
            out["waste"].append(max(0, made - demand))
        out["rev"].append(wrev - CHEF_WAGE_WEEK - wage_extra_week)
        out["rep"].append(rep)
    return out


def mc(seeds, **kw):
    res = [run(rng=random.Random(i), **kw) for i in range(seeds)]
    weeks = len(res[0]["rev"])
    rev = [statistics.mean(r["rev"][w] for r in res) for w in range(weeks)]
    rep = [statistics.mean(r["rep"][w] for r in res) for w in range(weeks)]
    s = statistics.mean(statistics.mean(r["s"]) for r in res)
    return rev, rep, s


# ------------------------------------------------------------ 打印

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

    print("## 1. 当天产能天花板（食材按文档上限 20/20/20/20/10，满库存）\n")
    md(static_table(), ["阶段", "产能min", "做A", "做B", "总份数", "最高日收入￥", "用掉min", "闲置min"])
    print("需求侧：来客 30 座 × (2~3) = 60~90 份/天；计划单示例写 50~100。\n")

    print("## 2. 食材不设限时，纯看时间能做多少份\n")
    md(time_only_table(), ["阶段", "产能min", "全做A份数", "全做B份数"])
    print("对照需求 60~90：W1 约 32 份(A) → 满足率 ≈0.43；W2 56 份 → ≈0.75；W3 84 份 → ≈1。\n")

    print("## 3. 满足率与风评日变化（需求取中值 75 份）\n")
    rows = []
    for name, mins in KITCHEN.items():
        for label, stock in (("食材上限20/20/20/20/10", full_stock()), ("食材无限", {k: 10**6 for k in CAP})):
            rev, a, b = best_plan(mins, stock, 75)
            served = a + b
            s = min(served / 75, 1)
            rows.append((name, label, a, b, served, f"{s:.2f}", f"{K*(s-S0):+.3f}", rev))
    md(rows, ["阶段", "食材", "A", "B", "份数", "满足率s", "Δ风评/天", "日收入￥"])

    print("## 4. 一周总账：食材上限 20 当作『仓库上限』（肉鸽一周补一次，补满）\n")
    rows = []
    for name, mins in KITCHEN.items():
        # 一周内仓库只有 20/20/20/20/10，一周最多做完这些
        rev_wk, a, b = best_plan(10**6, full_stock(), 10**9)
        rows.append((name, a, b, a + b, rev_wk, CHEF_WAGE_WEEK, f"{CHEF_WAGE_WEEK/rev_wk:.0%}", f"{(a+b)/(7*75):.1%}"))
    md(rows, ["阶段", "A", "B", "一周总份数", "一周最高收入￥", "厨师长周薪", "薪水占收入", "占周需求(约525份)"])
    print("（W1~W3 在这个口径下结果相同——产能根本用不上，一周就是 30 份。）\n")

    print("## 5. 要把产能吃满，一周需要多少食材（每种）\n")
    rows = []
    for name, mins in KITCHEN.items():
        wk = mins * 7
        rows.append((name, wk, wk // 30, wk // 50))
    md(rows, ["阶段", "一周总分钟", "全做A要几套(肉+菜)", "全做B要几套(肉+菜+调味)"])
    print("对比库存上限 20（调味 10）。\n")

    print("## 6. 风评涨速与特殊单（解析）\n")
    rows = [
        ("满座全喂饱", "+0.100", "—"),
        ("特殊单 1 个/天", "+0.150", "1.5×"),
        ("特殊单 2 个/天（上限）", "+0.300", "3×"),
        ("满座喂饱 + 2 个特殊单", "+0.400", "4×"),
        ("暴毙期望（有 B 菜时）", "−0.015", "−0.15×"),
        ("s=0.53 一天", "−0.370", "−3.7×"),
    ]
    md(rows, ["情景", "Δ风评/天", "相对『满座喂饱』"])
    for label, per_day in (("只靠满足率", 0.1), ("满足率 + 每天 1 个特殊单", 0.25), ("满足率 + 每天 2 个特殊单", 0.4)):
        print(f"- {label}：每天 +{per_day} → 40 周 {per_day*280:.0f} 分，60 周 {per_day*420:.0f} 分，满分 100 要 {100/per_day/7:.0f} 周")
    print()

    print("## 7. 蒙特卡洛（%d 次，52 周）：风评→来客是『假设』\n" % seeds)
    print("来客 = 座位 × 风评/100（线性假设）；食材每天回满（最乐观口径）。\n")
    rows = []
    for rep0 in (20, 50, 80):
        for name in ("W1", "W2", "W3"):
            for sp in (0, 2):
                rev, rep, s = mc(seeds, kitchen=name, rep0=rep0, mapping="线性", weeks=52, daily_refill=True,
                                 weekly_supply=0, p_special=sp, wage_extra_week=0)
                rows.append((rep0, name, sp, f"{rep[7]:.1f}", f"{rep[25]:.1f}", f"{rep[51]:.1f}",
                             f"{statistics.mean(rev[:8]):.0f}", f"{statistics.mean(rev[-8:]):.0f}", f"{s:.2f}"))
    md(rows, ["初始风评", "阶段", "特殊单/天", "第8周风评", "第26周", "第52周", "前8周均周净收入", "末8周均周净收入", "平均s"])

    print("## 8. 食材走仓库口径（每周补 N 套，封顶上限）：52 周周净收入\n")
    rows = []
    for supply in (5, 10, 20, 40):
        for name in ("W1", "W3"):
            rev, rep, s = mc(seeds, kitchen=name, rep0=50, mapping="线性", weeks=52, daily_refill=False,
                             weekly_supply=supply, p_special=0, wage_extra_week=0)
            rows.append((supply, name, f"{statistics.mean(rev):.0f}", f"{rep[-1]:.1f}", f"{s:.2f}"))
    md(rows, ["每周补(每种)", "阶段", "周净收入均值￥", "第52周风评", "平均s"])

    print("## 9. 座位升级到底赚不赚（食材每天回满、W3、特殊单 0；座位只在『需求<供给』时才有用）\n")
    rows = []
    for rep0 in (20, 50):
        base = None
        for seats, label, cost in ((30, "30座(初始)", 0), (40, "40座(桌子升级 10000￥)", 10000), (80, "80座(二楼 100000￥，假设新增 10 桌×4 座)", 110000)):
            rev, rep, s = mc(seeds, kitchen="W3", rep0=rep0, mapping="线性", weeks=52, daily_refill=True,
                             weekly_supply=0, p_special=0, wage_extra_week=0, seats=seats)
            tot = sum(rev)
            if base is None:
                base = tot
            gain = tot - base
            rows.append((rep0, label, f"{tot:.0f}", f"{gain:+.0f}", f"{cost}", "—" if gain <= 0 or cost == 0 else f"{cost / (gain / 52):.0f} 周"))
    md(rows, ["初始风评", "座位", "52 周净收入合计￥", "比 30 座多赚￥", "累计花费￥", "回本"])


if __name__ == "__main__":
    main()
