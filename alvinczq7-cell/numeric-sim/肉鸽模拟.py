# -*- coding: utf-8 -*-
"""
肉鸽部分数值模拟（复用橙子的 Shadorange/character/角色1/game.py 引擎，原文件不改）

用法：  python 肉鸽模拟.py               打印全部结果（Markdown 表格）
        python 肉鸽模拟.py --runs 600

做的事：
  · 用 game.py 的卡、怪、战斗结算原样跑，机器人代替玩家出牌
  · 修正模式：把 game.py 里和企划书不一致的地方补上（见 README 差异表），对比
  · 扫体力总量 / 战后回血 / 怪物数值倍率，看通关率与每层消耗
  · 单卡测试：起手卡组 + 2 张某卡，逐只打 7 个遭遇，看这张卡强不强
机器人只是一个『凑合会打』的策略，用来看相对关系，不代表玩家上限。
"""
import contextlib
import importlib.util
import io
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAME_PATH = os.path.normpath(os.path.join(HERE, "..", "..", "Shadorange", "character", "角色1", "game.py"))
spec = importlib.util.spec_from_file_location("game", GAME_PATH)
game = importlib.util.module_from_spec(spec)
spec.loader.exec_module(game)

# ------------------------------------------------------------ 修正模式

_orig_enemy_act = game.enemy_act


def _enemy_act_patched(player, enemy, log):
    it = enemy["intents"][enemy["i"] % len(enemy["intents"])]
    if it[0] == "entangle":                      # game.py 里没有处理这个意图
        enemy["i"] += 1
        player.entangle += it[1]
        return
    if it[0] == "multi":                         # 一回合多个意图
        enemy["i"] += 1
        saved = (enemy["intents"], enemy["i"])
        for sub in it[1]:
            enemy["intents"], enemy["i"] = [sub], 0
            if sub[0] == "entangle":
                player.entangle += sub[1]
            else:
                _orig_enemy_act(player, enemy, log)
        enemy["intents"], enemy["i"] = saved
        return
    _orig_enemy_act(player, enemy, log)


def apply_fidelity(on):
    """on=True：按企划书补上 game.py 漏掉的意图；False：原样。"""
    game.enemy_act = _enemy_act_patched if on else _orig_enemy_act
    E = game.E
    if on:
        game.ENEMIES["敌怪6"] = lambda: E("敌怪6", 40, [
            ("multi", [("blk", 7), ("debuff", "脆弱"), ("debuff", "缓慢")]),
            ("multi", [("atk", 10, 1), ("rage", 3)]),
            ("atk", 6, 3)])
        game.ENEMIES["敌怪7"] = lambda: E("敌怪7", 38, [
            ("atk", 1, 4), ("multi", [("drain", 9), ("rage", 2)]), ("atk", 3, 4)])
    else:
        game.ENEMIES["敌怪6"] = lambda: E("敌怪6", 40, [("blk", 7), ("atk", 10, 1), ("rage", 3), ("atk", 6, 3)])
        game.ENEMIES["敌怪7"] = lambda: E("敌怪7", 38, [("atk", 1, 4), ("drain", 9), ("atk", 3, 4)])


def scale_enemies(hp_mult=1.0, dmg_mult=1.0):
    """把所有怪物生命 / 攻击伤害乘倍率（只用于假设扫描）。"""
    base = {k: v for k, v in game.ENEMIES.items()}
    store = getattr(scale_enemies, "_orig", None)
    if store is None:
        scale_enemies._orig = store = base
    for k, f in store.items():
        def make(f=f):
            def g():
                e = f()
                e["hp"] = e["max_hp"] = max(1, round(e["hp"] * hp_mult))
                new = []
                for it in e["intents"]:
                    new.append(_scale_intent(it, dmg_mult))
                e["intents"] = new
                return e
            return g
        game.ENEMIES[k] = make()


def _scale_intent(it, m):
    if it[0] == "atk":
        return ("atk", max(1, round(it[1] * m)), it[2])
    if it[0] == "multi":
        return ("multi", [_scale_intent(s, m) for s in it[1]])
    return it


# ------------------------------------------------------------ 机器人

ATK_VAL = {"打击": 6, "重击": 20, "双重打击": 10, "盾反": 5, "迅捷打击": 7, "横劈": 7, "全力打击": 17, "多重打击": 0}
BLOCK_VAL = {"防御": 5, "盾反": 5, "招架": 8, "闪避": 6, "重甲": 13}
POWERS = ("越战越勇", "拉伸", "刺伤", "省力")
REWARD_RANK = ["越战越勇", "刺伤", "多重打击", "锻炼", "双重释放", "迅捷打击", "盾反", "疾速", "闪避",
               "全力打击", "横劈", "双重打击", "招架", "拉伸", "省力", "激怒", "重甲", "凝神", "透支"]


def incoming(p, enemies):
    tot = 0
    for e in enemies:
        it = e["intents"][e["i"] % len(e["intents"])]
        if it[0] == "multi":
            subs = it[1]
        else:
            subs = [it]
        for s in subs:
            if s[0] == "atk":
                tot += (s[1] + e["strength"]) * s[2] + e["rage"]
            elif s[0] == "drain":
                tot += s[1] + e["strength"]
    if p.vuln:
        tot = int(tot * 1.5)
    return tot


def est_dmg(p, c):
    if c == "多重打击":
        n = sum(1 for x in p.hand if game.CARDS[x]["kind"] == "攻击")
        return 6 * n
    base = ATK_VAL.get(c, 0)
    return base + (p.strength if base else 0)


def make_policy(mode):
    """mode: '稳'（挡得住才打）/ '莽'（只打不挡）/ '随机'（随机出牌，作为下限）"""
    def policy(p, enemies):
        if enemies is None:                                  # 战后选卡
            if mode == "随机":
                return str(random.randint(1, 3))
            return "__reward__"
        if p.stamina <= 0 or not p.hand:
            return "e"
        hand = p.hand
        if mode == "随机":
            return str(random.randint(1, len(hand))) if random.random() < 0.85 else "e"
        idx = {c: i for i, c in enumerate(hand)}

        def pick(c):
            return str(hand.index(c) + 1)

        # 能力牌 / 永久增益先出
        for c in POWERS + ("锻炼",):
            if c in hand and (c not in p.powers):
                return pick(c)
        alive = [e for e in enemies if e["hp"] > 0]
        # 能不能一回合清场
        atk_cards = [c for c in hand if ATK_VAL.get(c) is not None and c in ATK_VAL]
        total_atk = sum(est_dmg(p, c) for c in atk_cards)
        tot_hp = sum(e["hp"] + e["block"] for e in alive)
        # 增伤配套
        has_big = any(c in hand for c in ("重击", "全力打击"))
        if "双重释放" in hand and has_big:
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
                blocks.sort(key=lambda c: -BLOCK_VAL[c])
                # 招架在对方打得多时更值
                return pick(blocks[0])
        if "疾速" in hand and p.stamina > 6 and len(atk_cards) < 2:
            return pick("疾速")
        if atk_cards:
            # 多目标优先横劈；其他按期望伤害
            best = max(atk_cards, key=lambda c: (est_dmg(p, c) * (len(alive) if c == "横劈" else 1)))
            return pick(best)
        blocks = [c for c in hand if c in BLOCK_VAL]
        if blocks and need > 0:
            return pick(max(blocks, key=lambda c: BLOCK_VAL[c]))
        if "疾速" in hand:
            return pick("疾速")
        return "e"
    return policy


def reward_choice(mode, picks):
    if mode == "随机":
        return random.randint(1, len(picks))
    best = min(picks, key=lambda c: REWARD_RANK.index(c) if c in REWARD_RANK else 99)
    return picks.index(best) + 1


# ------------------------------------------------------------ 一局

_turn_counter = [0]
_orig_start_turn = game.Player.start_turn


def _count_turn(self):
    _turn_counter[0] += 1
    return _orig_start_turn(self)


game.Player.start_turn = _count_turn


def run_once(mode, stamina, heal, seed, hp=None):
    random.seed(seed)
    game.RUN_STAMINA = stamina
    game.HEAL_AFTER_BATTLE = heal
    if hp:
        game.START_HP = hp
    pol = make_policy(mode)
    p = game.Player(game.STARTER_DECK)
    floors = []
    cleared = 0
    cause = "通关"
    for name, wave in game.FLOORS:
        enemies = [game.ENEMIES[k]() for k in ("三小只A", "三小只B", "三小只C")] if wave == "三小只" else [game.ENEMIES[wave]()]
        hp0, st0, t0 = p.hp, p.stamina, _turn_counter[0]
        ok = game.battle(p, enemies, name, pol)
        floors.append(dict(name=name, hp_lost=hp0 - max(0, p.hp), st=st0 - p.stamina, turns=_turn_counter[0] - t0, ok=ok))
        if not ok:
            cause = "体力耗尽" if p.stamina <= 0 else "战死"
            break
        cleared += 1
        p.hp = min(p.max_hp, p.hp + heal)
        if wave != "大树精":
            pool = list(game.REWARD_POOL)
            random.shuffle(pool)
            picks = pool[:3]
            if mode != "随机" or True:
                c = picks[reward_choice(mode, picks) - 1]
                p.deck.append(c)
        if p.stamina <= 0:
            cause = "体力耗尽(回店)"
            break
    return dict(win=cleared == len(game.FLOORS), cleared=cleared, stamina=p.stamina, hp=p.hp,
                floors=floors, cause=cause, deck=len(p.deck))


@contextlib.contextmanager
def quiet():
    with contextlib.redirect_stdout(io.StringIO()):
        yield


def batch(runs, mode="稳", stamina=100, heal=5, hp=50):
    res = []
    with quiet():
        for i in range(runs):
            res.append(run_once(mode, stamina, heal, i, hp))
    return res


def summarize(res):
    n = len(res)
    win = sum(r["win"] for r in res) / n
    cl = statistics.mean(r["cleared"] for r in res)
    st = statistics.mean(r["stamina"] for r in res)
    return win, cl, st


def md(rows, head):
    print("| " + " | ".join(head) + " |")
    print("|" + "---|" * len(head))
    for r in rows:
        print("| " + " | ".join(str(x) for x in r) + " |")
    print()


# ------------------------------------------------------------ 输出

# game.py 的 7 层没用到企划书里的敌怪6 / 敌怪7，单独测一下
EXTRA = [("（企划书强怪）敌怪6", "敌怪6"), ("（企划书强怪）敌怪7", "敌怪7")]

def main():
    runs = 400
    if "--runs" in sys.argv:
        runs = int(sys.argv[sys.argv.index("--runs") + 1])
    game.START_HP = 50

    print(f"## A. 卡牌效率（静态，每张牌 1 点体力）\n")
    rows = []
    for c, d in game.CARDS.items():
        ops = d["ops"]
        dmg = sum(o[1] for o in ops if o[0] == "dmg")
        blk = sum(o[1] for o in ops if o[0] == "block")
        if c == "横劈":
            dmg = "7×敌人数"
        elif c == "多重打击":
            dmg = "6×手牌攻击数"
        rows.append((c, d["kind"], d["text"], dmg or "", blk or ""))
    md(rows, ["卡", "类型", "效果", "单体伤害/体力", "格挡/体力"])

    for fid, label in ((False, "原型原样"), (True, "按企划书补全")):
        print(f"## B. 起手卡组 vs 每个遭遇（{label}；不带战后回血与加卡，每场新开 50 血）\n")
        apply_fidelity(fid)
        rows_b = encounter_table(runs)
        md(rows_b, ["遭遇", "机器人胜率", "平均回合", "平均掉血", "平均出牌(=体力)", "血量占比"])

    print("## C. 一整局（七层）：原样 vs 按企划书补全\n")
    rows = []
    for fid, label in ((False, "原样"), (True, "补全（缠绕/脆弱/缓慢/怒气生效）")):
        apply_fidelity(fid)
        for mode in ("稳", "莽", "随机"):
            res = batch(runs, mode)
            w, cl, st = summarize(res)
            rows.append((label, mode, f"{w:.0%}", f"{cl:.2f}/7", f"{st:.1f}"))
    md(rows, ["版本", "机器人", "通关率", "平均推进", "剩余体力"])

    apply_fidelity(True)
    print("## D. 每层消耗（补全版，机器人『稳』，体力 100，每场回 5 血）\n")
    res = batch(runs, "稳")
    rows = []
    for k, (name, _) in enumerate(game.FLOORS):
        got = [r["floors"][k] for r in res if len(r["floors"]) > k]
        if not got:
            continue
        rows.append((name, len(got), f"{statistics.mean(x['hp_lost'] for x in got):.1f}",
                     f"{statistics.mean(x['st'] for x in got):.1f}", f"{statistics.mean(x['turns'] for x in got):.1f}",
                     f"{sum(x['ok'] for x in got)/len(got):.0%}"))
    md(rows, ["层", "到达局数", "平均掉血", "平均体力消耗", "平均回合", "该层胜率"])
    st_used = statistics.mean(100 - r["stamina"] for r in res if r["win"]) if any(r["win"] for r in res) else float("nan")
    print(f"通关局平均总耗体力：{st_used:.1f} / 100；失败原因分布：",
          {c: sum(1 for r in res if r['cause'] == c) for c in set(r['cause'] for r in res)}, "\n")

    print("## D2. 同上，但怪物生命×2（体力 100）\n")
    scale_enemies(2.0, 1.0)
    res = batch(runs, "稳")
    scale_enemies(1.0, 1.0)
    rows = []
    for k, (name, _) in enumerate(game.FLOORS):
        got = [r["floors"][k] for r in res if len(r["floors"]) > k]
        if not got:
            continue
        rows.append((name, len(got), f"{statistics.mean(x['hp_lost'] for x in got):.1f}",
                     f"{statistics.mean(x['st'] for x in got):.1f}", f"{statistics.mean(x['turns'] for x in got):.1f}",
                     f"{sum(x['ok'] for x in got)/len(got):.0%}"))
    md(rows, ["层", "到达局数", "平均掉血", "平均体力消耗", "平均回合", "该层胜率"])

    print("## E. 整局体力扫描（补全版，『稳』）\n")
    rows = []
    for stam in (30, 40, 50, 60, 70, 80, 100, 120):
        res = batch(runs, "稳", stamina=stam)
        w, cl, st = summarize(res)
        causes = {c: sum(1 for r in res if r['cause'] == c) for c in set(r['cause'] for r in res)}
        rows.append((stam, f"{w:.0%}", f"{cl:.2f}/7", f"{st:.1f}", causes))
    md(rows, ["整局体力", "通关率", "平均推进", "剩余体力", "结局分布"])

    print("## F. 战后回血扫描（体力 100，补全版）\n")
    rows = []
    for heal in (0, 5, 10):
        res = batch(runs, "稳", heal=heal)
        w, cl, st = summarize(res)
        rows.append((heal, f"{w:.0%}", f"{cl:.2f}/7", f"{st:.1f}"))
    md(rows, ["战后回血", "通关率", "平均推进", "剩余体力"])

    print("## G. 怪物数值倍率（橙子提的『大幅加强怪物数值』；体力 100，补全版）\n")
    rows = []
    for hm, dm in ((1.0, 1.0), (1.5, 1.0), (2.0, 1.0), (1.0, 1.5), (1.5, 1.5), (2.0, 1.5), (2.0, 2.0)):
        scale_enemies(hm, dm)
        res = batch(runs, "稳")
        w, cl, st = summarize(res)
        used = [100 - r["stamina"] for r in res]
        rows.append((f"×{hm}", f"×{dm}", f"{w:.0%}", f"{cl:.2f}/7", f"{statistics.mean(used):.1f}"))
    scale_enemies(1.0, 1.0)
    md(rows, ["怪物生命", "怪物伤害", "通关率", "平均推进", "平均耗体力"])

    print("## H. 双倍怪物 × 体力扫描（找『体力成为取舍』的区间）\n")
    rows = []
    scale_enemies(2.0, 1.0)
    for stam in (60, 80, 100, 120, 150):
        res = batch(runs, "稳", stamina=stam)
        w, cl, st = summarize(res)
        rows.append((stam, f"{w:.0%}", f"{cl:.2f}/7", f"{st:.1f}"))
    scale_enemies(1.0, 1.0)
    md(rows, ["整局体力", "通关率(怪生命×2)", "平均推进", "剩余体力"])

    print("## I. 单卡测试：起手 + 2 张某卡，逐遭遇打，不回血，每场新开 50 血\n")
    rows = single_card_table(max(30, runs // 8))
    md(rows, ["加的卡", "平均掉血", "平均出牌", "相对起手：掉血", "相对起手：出牌"])


def encounter_table(runs, extra=None):
    rows = []
    with quiet():
        for k, (name, wave) in enumerate(game.FLOORS + EXTRA):
            res = []
            for i in range(runs):
                random.seed(i)
                game.RUN_STAMINA = 10_000
                pol = make_policy("稳")
                p = game.Player(list(game.STARTER_DECK) + list(extra or []))
                enemies = [game.ENEMIES[x]() for x in ("三小只A", "三小只B", "三小只C")] if wave == "三小只" else [game.ENEMIES[wave]()]
                t0 = _turn_counter[0]
                ok = game.battle(p, enemies, name, pol)
                res.append((ok, _turn_counter[0] - t0, 50 - max(0, p.hp), 10_000 - p.stamina))
            rows.append((name, f"{sum(r[0] for r in res)/runs:.0%}", f"{statistics.mean(r[1] for r in res):.1f}",
                         f"{statistics.mean(r[2] for r in res):.1f}", f"{statistics.mean(r[3] for r in res):.1f}",
                         f"{statistics.mean(r[2] for r in res)/50:.0%}"))
    return rows


def single_card_table(runs):
    apply_fidelity(True)

    def avg(extra):
        hl, st = [], []
        with quiet():
            for k, (name, wave) in enumerate(game.FLOORS):
                for i in range(runs):
                    random.seed(i * 7 + k)
                    game.RUN_STAMINA = 150
                    pol = make_policy("稳")
                    p = game.Player(list(game.STARTER_DECK) + extra)
                    enemies = [game.ENEMIES[x]() for x in ("三小只A", "三小只B", "三小只C")] if wave == "三小只" else [game.ENEMIES[wave]()]
                    game.battle(p, enemies, name, pol)
                    hl.append(50 - max(0, p.hp))
                    st.append(150 - p.stamina)
        return statistics.mean(hl), statistics.mean(st)

    base_h, base_s = avg([])
    rows = [("（起手卡组）", f"{base_h:.1f}", f"{base_s:.1f}", "—", "—")]
    out = []
    for c in game.REWARD_POOL:
        h, s = avg([c, c])
        out.append((h - base_h, c, h, s))
    out.sort()
    for d, c, h, s in out:
        rows.append((c, f"{h:.1f}", f"{s:.1f}", f"{d:+.1f}", f"{s-base_s:+.1f}"))
    return rows


if __name__ == "__main__":
    main()
