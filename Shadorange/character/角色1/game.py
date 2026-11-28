# -*- coding: utf-8 -*-
"""
《Selene's Black Tide Restaurant》· 肉鸽部分 文本试玩原型

用法：
    python game.py            正常开局
    python game.py --seed 42  固定随机种子

原型参数（橙子定的）：
    · 整局体力 100 点，出牌消耗，见底回店
    · 所有卡牌耗 1 点体力
    · 没有回血：打完不会自己回血，血就是一路往下掉
    · 能力牌打出后消耗（进「消耗」堆，本局不再出现，但能力效果保留）
    · 牌库按 抽牌堆 / 手牌 / 弃牌堆 / 消耗堆 四堆运作
    · 层数无上限，敌怪分布以 7 层为一个循环

数据来源：docs/00-overview/游戏企划书.md（角色 1 全套卡 + 地图 1 敌怪）
未实现：史莱姆合体、遗物、事件房、卡牌升级（都不影响这一版的骨架验证）
"""

import random
import sys

# 老式 Windows 控制台可能是 GBK 代码页，▶ █ 这类符号编不出来会直接抛
# UnicodeEncodeError 把游戏打断。这里降级成 ? 而不是崩掉。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except Exception:
        pass

# ---------------------------------------------------------------- 参数

RUN_STAMINA = 100        # 整局体力
CARD_COST = 1            # 所有卡牌统一 1 点
START_HP = 50            # 角色 1 初始生命
DRAW_PER_TURN = 6        # 5 张基础 + 角色能力 1 张
MAX_HAND = 10
CYCLE = 7                # 7 层一个循环，层数本身无上限

# ---------------------------------------------------------------- 卡库

# ops 是效果指令序列，按顺序执行：
#   ("dmg", n)        单体 n 点，一次
#   ("dmg_all", n)    全体 n 点
#   ("dmg_hand", n)   n 点 × 手牌中攻击牌数（含本张）
#   ("block", n)      获得 n 点格挡
#   ("draw", n)       抽 n 张
#   ("str", n)        力量 +n（永久）
#   ("dex", n)        敏捷 +n（下次防御）
#   ("rage", n)       怒气 +n（加进下一次攻击）
#   ("thorns",)       本回合反弹被格挡的伤害
#   ("double_next",)  下一张牌打两次
#   ("weak_self",)    自身下回合攻击 -50%
#   ("slow_self",)    自身下回合防御 -25%
#   ("flat_penalty", n) 自身下回合攻击 -n
#   ("power", 名称)   获得局内能力（出局清空）

CARDS = {
    # —— 初始卡组 ——
    "打击": {"kind": "攻击", "text": "打 6", "ops": [("dmg", 6)]},
    "防御": {"kind": "技能", "text": "防 5", "ops": [("block", 5)]},
    "重击": {"kind": "攻击", "text": "打 20", "ops": [("dmg", 20)]},

    # —— 可选 · 攻击 ——
    "双重打击": {"kind": "攻击", "text": "打 5×2", "ops": [("dmg", 5), ("dmg", 5)]},
    "盾反": {"kind": "攻击", "text": "打 5 防 5", "ops": [("dmg", 5), ("block", 5)]},
    "迅捷打击": {"kind": "攻击", "text": "打 7 抽 1", "ops": [("dmg", 7), ("draw", 1)]},
    "横劈": {"kind": "攻击", "text": "全体 7", "ops": [("dmg_all", 7)]},
    "全力打击": {"kind": "攻击", "text": "打 25，自身虚弱",
                "ops": [("dmg", 25), ("weak_self",)]},
    "多重打击": {"kind": "攻击", "text": "打 6 × 手牌攻击数",
                "ops": [("dmg_hand", 6)]},

    # —— 可选 · 技能 ——
    "激怒": {"kind": "技能", "text": "怒气 +5", "ops": [("rage", 5)]},
    "凝神": {"kind": "技能", "text": "敏捷 +4", "ops": [("dex", 4)]},
    "疾速": {"kind": "技能", "text": "抽 3", "ops": [("draw", 3)]},
    "招架": {"kind": "技能", "text": "防 8 反弹", "ops": [("block", 8), ("thorns",)]},
    "闪避": {"kind": "技能", "text": "防 6 抽 2", "ops": [("block", 6), ("draw", 2)]},
    "透支": {"kind": "技能", "text": "怒气 +10，下回合打 -3",
             "ops": [("rage", 10), ("flat_penalty", 3)]},
    "双重释放": {"kind": "技能", "text": "下一张牌打两次", "ops": [("double_next",)]},
    "重甲": {"kind": "技能", "text": "防 13，下回合防 -25%",
             "ops": [("block", 13), ("slow_self",)]},
    "锻炼": {"kind": "技能", "text": "力量 +2", "ops": [("str", 2)]},

    # —— 可选 · 能力 ——
    "越战越勇": {"kind": "能力", "text": "每造成 10 伤抽 1", "ops": [("power", "越战越勇")]},
    "省力": {"kind": "能力", "text": "每第 4 张牌免费", "ops": [("power", "省力")]},
    "拉伸": {"kind": "能力", "text": "每造成 5 伤得 1 格挡", "ops": [("power", "拉伸")]},
    "刺伤": {"kind": "能力", "text": "每次伤害施加 1 层流血", "ops": [("power", "刺伤")]},
}

STARTER_DECK = ["打击"] * 4 + ["防御"] * 4 + ["重击"]
REWARD_POOL = [c for c in CARDS if c not in ("打击", "防御", "重击")]

# ---------------------------------------------------------------- 敌怪

def E(name, hp, intents, kind=None):
    return {"name": name, "hp": hp, "max_hp": hp, "block": 0, "strength": 0,
            "rage": 0, "bleed": 0, "i": 0, "intents": intents, "kind": kind}


# 意图格式：("atk", 伤害, 次数) / ("str", n) / ("blk", n) / ("debuff", 名称)
#          / ("drain", n) / ("rage", n) / ("entangle", n) / ("multi", [子意图...])
# 数值全部来自橙子 2026-11-28 给的怪物表，未做任何调整。
ENEMIES = {
    # —— 弱怪 ——
    "敌怪1": lambda: E("敌怪1", 50, [("atk", 11, 1), ("str", 5), ("atk", 16, 1)]),
    "敌怪2": lambda: E("敌怪2", 55, [("debuff", "虚弱"), ("str", 10), ("atk", 23, 1)]),
    "敌怪3": lambda: E("敌怪3", 45, [("multi", [("atk", 10, 1), ("blk", 5)]), ("str", 5),
                                     ("multi", [("atk", 15, 1), ("blk", 5)])]),
    # —— 强怪 ——
    "敌怪5": lambda: E("敌怪5", 63, [("atk", 19, 1), ("multi", [("blk", 6), ("str", 5)]),
                                     ("atk", 10, 2)]),
    "敌怪6": lambda: E("敌怪6", 60, [("multi", [("blk", 7), ("debuff", "脆弱"), ("debuff", "缓慢")]),
                                     ("multi", [("atk", 18, 1), ("rage", 3)]), ("atk", 8, 3)]),
    "敌怪7": lambda: E("敌怪7", 50, [("atk", 3, 4), ("multi", [("drain", 9), ("rage", 2)]),
                                     ("atk", 5, 4)]),
    # —— 精英 ——
    "精英1": lambda: E("精英1", 92, [("atk", 18, 1), ("str", 5), ("atk", 23, 1)]),
    # —— Boss ——
    "大树精": lambda: E("大树精", 280, [("entangle", 6), ("atk", 21, 1), ("str", 5), ("atk", 26, 1)]),
    # —— 三小只（20 / 35 / 15）——
    "三小只A": lambda: E("三小只·20", 20, [("atk", 9, 1), ("str", 5), ("debuff", "缓慢")]),
    "三小只B": lambda: E("三小只·35", 35, [("debuff", "缓慢"), ("atk", 16, 1), ("atk", 6, 1)]),
    "三小只C": lambda: E("三小只·15", 15, [("atk", 9, 1), ("str", 5), ("debuff", "缓慢")]),
}


def small_slime(hp=20, name="史莱姆·小只"):
    return E(name, hp, [("atk", 4, 1), ("multi", [("debuff", "虚弱"), ("str", 2)]),
                        ("atk", 6, 1)], kind="小只")


def medium_slime(hp=30):
    return E("史莱姆·中只", hp, [("atk", 8, 1), ("multi", [("debuff", "虚弱"), ("str", 4)]),
                                 ("atk", 12, 1)], kind="中只")


# 7 层一个循环。第 5 层强怪、第 6 层精英随机，第 7 层大树精。
FLOORS = [
    ("入口·苔径", "敌怪1"),
    ("积水走廊", "敌怪2"),
    ("碎石阶", "敌怪3"),
    ("湿洞", "三小只"),
    ("巢穴外缘", "强怪"),
    ("精英·锈铁门", "精英"),
    ("树心", "大树精"),
]

STRONG_POOL = ["敌怪5", "敌怪6", "敌怪7"]
ELITE_POOL = ["精英1", "精英2"]


def make_enemies(wave):
    if wave == "三小只":
        return [ENEMIES["三小只A"](), ENEMIES["三小只B"](), ENEMIES["三小只C"]()]
    if wave == "强怪":
        return [ENEMIES[random.choice(STRONG_POOL)]()]
    if wave == "精英":
        return make_enemies(random.choice(ELITE_POOL))
    if wave == "精英2":
        return [small_slime() for _ in range(4)]
    return [ENEMIES[wave]()]


def cleanup_enemies(enemies, log):
    """清掉死掉的敌人；中只被击败会裂成两只 10 血小只。"""
    out = []
    for e in enemies:
        if e["hp"] > 0:
            out.append(e)
        elif e.get("kind") == "中只":
            out.extend([small_slime(10, "史莱姆·小只(裂)") for _ in range(2)])
            log.append(f"  {e['name']} 被击碎，裂成两只 10 血小只")
    enemies[:] = out


def slime_merge(enemies, log):
    """玩家回合结束时：血量 ≤6 的小只和相邻小只合体成 30 血中只；
    还有残血小只的，继续融进中只，每只 +15 血。"""
    changed = True
    while changed:
        changed = False
        for i in range(len(enemies) - 1):
            a, b = enemies[i], enemies[i + 1]
            if (a.get("kind") == "小只" and b.get("kind") == "小只"
                    and (a["hp"] <= 6 or b["hp"] <= 6)):
                log.append(f"  {a['name']} 与 {b['name']} 合体 → 中只（30 血）")
                enemies[i:i + 2] = [medium_slime()]
                changed = True
                break
        if changed:
            continue
        for i, e in enumerate(enemies):
            if e.get("kind") == "小只" and e["hp"] <= 6 and e["hp"] > 0:
                med = next((x for x in enemies if x.get("kind") == "中只" and x["hp"] > 0), None)
                if med:
                    med["max_hp"] += 15
                    med["hp"] += 15
                    log.append(f"  {e['name']} 融进中只，中只 +15 血（{med['hp']}）")
                    enemies.pop(i)
                    changed = True
                    break

LOOT_TABLE = ["神秘肉类", "神秘调料", "高级升级素材", "增益道具"]

# ---------------------------------------------------------------- 工具

def hr(ch="─", n=52):
    return ch * n


def bar(cur, top, width=20):
    fill = 0 if top <= 0 else int(width * max(0, cur) / top)
    return "█" * fill + "░" * (width - fill)


def intent_text(it):
    k = it[0]
    if k == "atk":
        return f"打 {it[1]}" + (f"×{it[2]}" if it[2] > 1 else "")
    if k == "str":
        return f"力量 +{it[1]}"
    if k == "blk":
        return f"防 {it[1]}"
    if k == "debuff":
        return f"施加{it[1]}"
    if k == "drain":
        return f"吸血 {it[1]}"
    if k == "rage":
        return f"怒气 +{it[1]}"
    if k == "entangle":
        return f"缠绕 +{it[1]}"
    if k == "multi":
        return " + ".join(intent_text(x) for x in it[1])
    return "?"


# ---------------------------------------------------------------- 玩家

class Player:
    def __init__(self, deck):
        self.max_hp = START_HP
        self.hp = START_HP
        self.stamina = RUN_STAMINA
        self.deck = list(deck)
        self.block = 0
        self.strength = 0
        self.dexterity = 0
        self.rage = 0
        self.weak = 0
        self.slow = 0
        self.vuln = 0
        self.flat_penalty = 0
        self._weak_next = self._slow_next = self._vuln_next = self._flat_next = 0
        self.thorns = False
        self.thorns_bank = 0
        self.double_next = False
        self.powers = set()
        self.cards_played = 0
        self.dmg_counter = 0
        self.entangle = 0
        self.draw_pile, self.hand, self.discard, self.exhaust = [], [], [], []

    # —— 牌堆 ——
    def new_battle(self):
        self.draw_pile = list(self.deck)
        random.shuffle(self.draw_pile)
        self.hand, self.discard, self.exhaust = [], [], []
        self.block = 0
        self.entangle = 0
        self.thorns = False
        self.double_next = False

    def draw(self, n, log=None):
        got = 0
        for _ in range(n):
            if not self.draw_pile:
                if not self.discard:
                    break
                self.draw_pile = self.discard
                self.discard = []
                random.shuffle(self.draw_pile)
            if len(self.hand) >= MAX_HAND:
                break
            self.hand.append(self.draw_pile.pop())
            got += 1
        return got

    def start_turn(self):
        self.weak = self._weak_next
        self.slow = self._slow_next
        self.vuln = self._vuln_next
        self.flat_penalty = self._flat_next
        self._weak_next = self._slow_next = self._vuln_next = self._flat_next = 0
        self.block = 0
        self.thorns = False   # 招架只保本回合，敌方行动期间有效
        if self.entangle > 0 and self.hp > 0:
            self.hp -= self.entangle
            print(f"  ⚠ 缠绕发作，受到 {self.entangle} 点伤害")
        self.draw(DRAW_PER_TURN)

    def end_turn(self):
        self.discard.extend(self.hand)
        self.hand = []

    # —— 数值 ——
    def gain_block(self, n):
        if self.slow > 0:
            n = int(n * 0.75)
        n += self.dexterity
        if n > 0:
            self.block += n
            if self.dexterity > 0:
                self.dexterity = 0

    def take_damage(self, dmg):
        dmg = int(dmg)
        blocked = min(self.block, dmg)
        self.block -= blocked
        taken = dmg - blocked
        self.hp -= taken
        return taken, blocked


# ---------------------------------------------------------------- 战斗

def attack_enemy(player, enemy, base, log):
    """打一下敌人，返回实际造成的伤害"""
    dmg = base + player.strength
    if player.rage > 0:
        dmg += player.rage
        player.rage = 0
    if player.weak > 0:
        dmg //= 2
    if player.flat_penalty > 0:
        dmg = max(0, dmg - player.flat_penalty)
    if enemy["bleed"] > 0:
        dmg += enemy["bleed"]
        enemy["bleed"] = 0
    blocked = min(enemy["block"], dmg)
    enemy["block"] -= blocked
    dealt = dmg - blocked
    enemy["hp"] -= dealt

    # 能力触发
    if dealt > 0:
        player.dmg_counter += dealt
        if "越战越勇" in player.powers:
            while player.dmg_counter >= 10:
                player.dmg_counter -= 10
                player.draw(1)
                log.append("越战越勇：抽 1 张")
        if "拉伸" in player.powers:
            player.thorns_bank += dealt
            while player.thorns_bank >= 5:
                player.thorns_bank -= 5
                player.block += 1
        if "刺伤" in player.powers:
            enemy["bleed"] += 1
    return dealt


def play_card(player, name, enemies, log):
    card = CARDS[name]
    ops = list(card["ops"])
    double = player.double_next and name != "双重释放"
    player.double_next = False
    times = 2 if double else 1
    if double:
        log.append(f"双重释放生效：{name} 打出两次")

    for _ in range(times):
        for op in ops:
            k = op[0]
            if k == "dmg":
                target = next((e for e in enemies if e["hp"] > 0), None)
                if target:
                    d = attack_enemy(player, target, op[1], log)
                    log.append(f"{target['name']} 受到 {d} 点伤害")
            elif k == "dmg_all":
                for e in list(enemies):
                    if e["hp"] > 0:
                        d = attack_enemy(player, e, op[1], log)
                        log.append(f"{e['name']} 受到 {d} 点伤害")
            elif k == "dmg_hand":
                n = sum(1 for c in player.hand if CARDS[c]["kind"] == "攻击") + 1
                for _ in range(n):
                    target = next((e for e in enemies if e["hp"] > 0), None)
                    if target:
                        d = attack_enemy(player, target, op[1], log)
                        log.append(f"{target['name']} 受到 {d} 点伤害")
            elif k == "block":
                before = player.block
                player.gain_block(op[1])
                log.append(f"获得 {player.block - before} 点格挡")
            elif k == "draw":
                got = player.draw(op[1])
                log.append(f"抽 {got} 张")
            elif k == "str":
                player.strength += op[1]
                log.append(f"力量 +{op[1]}")
            elif k == "dex":
                player.dexterity += op[1]
                log.append(f"敏捷 +{op[1]}")
            elif k == "rage":
                player.rage += op[1]
                log.append(f"怒气 +{op[1]}")
            elif k == "thorns":
                player.thorns = True
                log.append("本回合反弹伤害")
            elif k == "double_next":
                player.double_next = True
                log.append("下一张牌将打出两次")
            elif k == "weak_self":
                player._weak_next = 1
                log.append("自身获得虚弱（下回合攻击 -50%）")
            elif k == "slow_self":
                player._slow_next = 1
                log.append("自身获得缓慢（下回合防御 -25%）")
            elif k == "flat_penalty":
                player._flat_next = max(player._flat_next, op[1])
                log.append(f"下回合攻击 -{op[1]}")
            elif k == "power":
                player.powers.add(op[1])
                log.append(f"获得能力：{op[1]}")

    player.cards_played += 1


def enemy_act(player, enemy, log):
    it = enemy["intents"][enemy["i"] % len(enemy["intents"])]
    enemy["i"] += 1
    apply_intent(player, enemy, it, log)


def apply_intent(player, enemy, it, log):
    k = it[0]
    if k == "multi":
        for sub in it[1]:
            apply_intent(player, enemy, sub, log)
        return
    if k == "atk":
        dmg, times = it[1], it[2]
        for _ in range(times):
            d = dmg + enemy["strength"]
            if enemy["rage"] > 0:
                d += enemy["rage"]
                enemy["rage"] = 0
            if player.vuln > 0:
                d = int(d * 1.5)
            taken, blocked = player.take_damage(d)
            log.append(f"  {enemy['name']} 攻击 {d}，你受到 {taken} 点伤害"
                       + (f"（格挡 {blocked}）" if blocked else ""))
            if blocked and player.thorns:
                enemy["hp"] -= blocked
                log.append(f"  招架反弹 {blocked} 点伤害")
    elif k == "str":
        enemy["strength"] += it[1]
        log.append(f"  {enemy['name']} 力量 +{it[1]}")
    elif k == "blk":
        enemy["block"] += it[1]
        log.append(f"  {enemy['name']} 获得 {it[1]} 点格挡")
    elif k == "debuff":
        if it[1] == "虚弱":
            player._weak_next = 1
        elif it[1] == "缓慢":
            player._slow_next = 1
        elif it[1] == "脆弱":
            player._vuln_next = 1
        log.append(f"  {enemy['name']} 对你施加 {it[1]}")
    elif k == "drain":
        taken, _ = player.take_damage(it[1] + enemy["strength"])
        enemy["hp"] = min(enemy["max_hp"], enemy["hp"] + taken)
        log.append(f"  {enemy['name']} 吸取 {it[1]} 血，回复 {taken} 点生命")
    elif k == "rage":
        enemy["rage"] += it[1]
        log.append(f"  {enemy['name']} 怒气 +{it[1]}")
    elif k == "entangle":
        player.entangle += it[1]
        log.append(f"  {enemy['name']} 对你叠加缠绕，现在 {player.entangle} 层"
                   f"（每回合掉 {player.entangle} 血）")


# ---------------------------------------------------------------- 显示

def show_state(player, enemies, turn):
    print()
    print(hr())
    print(f"第 {turn} 回合 · 生命 {max(0, player.hp)}/{player.max_hp} "
          f"[{bar(max(0, player.hp), player.max_hp)}]")
    print(f"体力 {player.stamina}/{RUN_STAMINA} [{bar(player.stamina, RUN_STAMINA)}]"
          f" · 格挡 {player.block}")
    piles = f"抽牌堆 {len(player.draw_pile)} · 弃牌堆 {len(player.discard)}"
    if player.exhaust:
        piles += f" · 消耗 {len(player.exhaust)}"
    print("  " + piles)
    st = []
    if player.strength:
        st.append(f"力量 {player.strength}")
    if player.dexterity:
        st.append(f"敏捷 {player.dexterity}")
    if player.rage:
        st.append(f"怒气 {player.rage}")
    if player.weak:
        st.append("虚弱")
    if player.slow:
        st.append("缓慢")
    if player.vuln:
        st.append("脆弱")
    if player.powers:
        st.append("能力：" + "/".join(sorted(player.powers)))
    print("  " + ("　".join(st) if st else "无状态"))
    print(hr())
    for idx, e in enumerate(enemies, 1):
        it = e["intents"][e["i"] % len(e["intents"])]
        extra = []
        if e["strength"]:
            extra.append(f"力量{e['strength']}")
        if e["block"]:
            extra.append(f"格挡{e['block']}")
        if e["bleed"]:
            extra.append(f"流血{e['bleed']}")
        print(f"  [{idx}] {e['name']}  {max(0, e['hp'])}/{e['max_hp']} "
              f"意图：{intent_text(it)}" + (f"  ({', '.join(extra)})" if extra else ""))
    print(hr())
    if not player.hand:
        print("  手牌已空")
    for i, c in enumerate(player.hand, 1):
        cs = "免费" if "省力" in player.powers and (player.cards_played + 1) % 4 == 0 else f"{CARD_COST}体"
        print(f"  {i}. {c}  [{CARDS[c]['kind']}·{cs}]  {CARDS[c]['text']}")
    print(hr())
    print("输入卡牌序号出牌，其他命令： e 结束回合 / i 说明 / q 退出")


# ---------------------------------------------------------------- 主流程

def battle(player, enemies, floor_name, policy=None):
    player.new_battle()
    turn = 1
    log = []
    while enemies and player.hp > 0 and turn <= 100:
        player.start_turn()
        if player.hp <= 0:
            break
        if player.stamina <= 0:
            print("\n体力见底，只能回店了。")
            return "retreat"
        while True:
            show_state(player, enemies, turn)
            if log:
                print()
                for l in log[-6:]:
                    print("  " + l)
                log = []
            cmd = policy(player, enemies) if policy else input("> ")
            cmd = str(cmd).strip().lower()
            if cmd == "q":
                print("\n已退出。")
                sys.exit(0)
            if cmd == "i":
                print(CARDS_HELP)
                continue
            if cmd == "e":
                player.end_turn()
                slime_merge(enemies, log)      # 玩家回合结束：史莱姆合体
                break
            if not cmd.isdigit() or not (1 <= int(cmd) <= len(player.hand)):
                print("  ✗ 没有这张牌")
                continue
            idx = int(cmd) - 1
            name = player.hand[idx]
            cost = CARD_COST
            if "省力" in player.powers and (player.cards_played + 1) % 4 == 0:
                cost = 0
            if player.stamina < cost:
                print("  ✗ 体力不够，只能结束回合了")
                continue
            player.hand.pop(idx)
            player.stamina -= cost
            print(f"\n▶ 打出 {name}  (体力 -{cost})")
            play_card(player, name, enemies, log)
            if CARDS[name]["kind"] == "能力":
                player.exhaust.append(name)
                log.append("（能力牌已消耗，本局不再回到牌堆）")
            else:
                player.discard.append(name)
            for l in log:
                print("  " + l)
            log = []
            cleanup_enemies(enemies, log)
            if not enemies:
                break
            if player.hp <= 0:
                break

        if not enemies or player.hp <= 0:
            break
        print()
        print(hr("·"))
        for e in list(enemies):
            enemy_act(player, e, log)
            if player.hp <= 0:
                break
        for l in log:
            print(l)
        log = []
        enemies[:] = [e for e in enemies if e["hp"] > 0]
        turn += 1

    if player.hp <= 0:
        return "dead"
    if enemies:
        return "retreat"          # 打满 100 回合还没结束，按撤退处理
    if player.stamina <= 0:
        return "retreat"
    print(f"\n✔ 清空「{floor_name}」")
    return "win"


def card_reward(player, policy=None):
    pool = [c for c in REWARD_POOL]
    random.shuffle(pool)
    picks = pool[:3]
    print("\n" + hr("═"))
    print("掉落：选择一张卡加入卡组（输入序号，回车跳过）")
    for i, c in enumerate(picks, 1):
        print(f"  {i}. {c}  [{CARDS[c]['kind']}]  {CARDS[c]['text']}")
    while True:
        s = policy(player, None) if policy else input("> ")
        s = str(s).strip()
        if s == "":
            print("  （跳过了）")
            return
        if s.isdigit() and 1 <= int(s) <= len(picks):
            player.deck.append(picks[int(s) - 1])
            print(f"  ✔ 加入 {picks[int(s) - 1]}")
            return
        print("  ✗ 输序号，或直接回车跳过")


CARDS_HELP = """
关键词：
  格挡      挡伤害，下回合开始清空
  力量      每次攻击 +1，跨回合保留
  敏捷      下一次获得格挡时 +1，用掉就没了
  怒气      加进下一次攻击，用掉就没了
  虚弱      攻击伤害 -50%
  缓慢      获得格挡 -25%
  脆弱      受到伤害 +50%
  流血      下一次受到的伤害 +层数，然后清空
"""


def main():
    global RUN_STAMINA
    seed = None
    if "--seed" in sys.argv:
        try:
            seed = int(sys.argv[sys.argv.index("--seed") + 1])
        except (IndexError, ValueError):
            pass
    if "--stamina" in sys.argv:
        try:
            RUN_STAMINA = int(sys.argv[sys.argv.index("--stamina") + 1])
        except (IndexError, ValueError):
            pass
    random.seed(seed)

    print(hr("═"))
    print("  《Selene's Black Tide Restaurant》")
    print("  肉鸽部分 · 文本试玩原型")
    print(hr("═"))
    print(f"  角色 1「无脑灌伤」  生命 {START_HP}  每回合抽 {DRAW_PER_TURN}")
    print(f"  整局体力 {RUN_STAMINA}，每张牌 {CARD_COST} 点")
    print("  没有回血，层数无上限：7 层一循环，看你能爬到第几层。")
    print(hr("═"))
    input("回车开始 >> ")

    player = Player(STARTER_DECK)
    run_run(player)


def floor_label(i):
    """第 i 层（0 起）显示名。层数无限，7 层一循环。"""
    name = FLOORS[i % CYCLE][0]
    cycle = i // CYCLE + 1
    return name if cycle == 1 else f"{name}（第 {cycle} 圈）"


def run_run(player, policy=None, max_floors=None):
    """跑一整局。层数无上限，7 层一循环。
    policy(player, enemies) -> 命令字符串；None 表示由玩家输入。"""
    loot = []
    cleared = 0
    cause = "回店"
    i = 0
    while max_floors is None or cleared < max_floors:
        floor_name, wave = FLOORS[i % CYCLE]
        label = floor_label(i)
        print("\n" + hr("═"))
        print(f"  ▶ 第 {cleared + 1} 层 · {label}   体力 {player.stamina}/{RUN_STAMINA}")
        print(hr("═"))
        if wave == "三小只":
            enemies = make_enemies("三小只")
        else:
            enemies = make_enemies(wave)
        res = battle(player, enemies, label, policy)
        if res == "dead":
            print("\n" + hr("═"))
            print(f"  ✘ 倒在第 {cleared + 1} 层「{label}」。")
            print("  没带回任何东西（原型规则：倒了 = 全丢）。")
            print(hr("═"))
            return {"win": False, "cleared": cleared, "loot": [],
                    "stamina": player.stamina, "cause": "生命归零"}
        if res == "retreat":
            cause = "体力见底"
            break
        cleared += 1
        if wave in ("精英", "大树精"):
            loot.append(random.choice(LOOT_TABLE))
        loot.append(random.choice(LOOT_TABLE))
        card_reward(player, policy)
        i += 1

    print("\n" + hr("═"))
    print(f"  ✔ 回店结算（{cause}）")
    print(f"  推进到第 {cleared} 层    卡组 {len(player.deck)} 张")
    print(f"  剩余体力 {player.stamina}/{RUN_STAMINA}    生命 {max(0, player.hp)}/{player.max_hp}")
    print(f"  战利品：{'、'.join(loot) if loot else '空手而归'}")
    print(hr("═"))
    print("  这些东西第二天营业能用（经营部分未实现）")
    return {"win": False, "cleared": cleared, "loot": loot,
            "stamina": player.stamina, "cause": cause}


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n已中断。")
