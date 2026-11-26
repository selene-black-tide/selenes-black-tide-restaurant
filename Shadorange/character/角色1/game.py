# -*- coding: utf-8 -*-
"""
《Selene's Black Tide Restaurant》· 肉鸽部分 文本试玩原型

用法：
    python game.py            正常开局
    python game.py --seed 42  固定随机种子

原型参数（橙子定的两条）：
    · 整局体力 100 点，出牌消耗，见底回店
    · 所有卡牌耗 1 点体力

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
HEAL_AFTER_BATTLE = 5    # 原型平衡用：每场战斗后回 5 血，不是设定
MAX_HAND = 10

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

def E(name, hp, intents):
    return {"name": name, "hp": hp, "max_hp": hp, "block": 0, "strength": 0,
            "rage": 0, "bleed": 0, "i": 0, "intents": intents}


# 意图格式：("atk", 伤害, 次数) / ("str", n) / ("blk", n) / ("debuff", 名称)
#          / ("drain", n) / ("rage", n)
ENEMIES = {
    "敌怪1": lambda: E("敌怪1", 30, [("atk", 7, 1), ("str", 3), ("atk", 10, 1)]),
    "敌怪2": lambda: E("敌怪2", 35, [("debuff", "虚弱"), ("str", 10), ("atk", 13, 1)]),
    "敌怪3": lambda: E("敌怪3", 24, [("atk", 5, 1), ("blk", 5), ("atk", 7, 1)]),
    "敌怪5": lambda: E("敌怪5", 47, [("atk", 9, 1), ("blk", 6), ("str", 5), ("atk", 7, 2)]),
    "敌怪6": lambda: E("敌怪6", 40, [("blk", 7), ("atk", 10, 1), ("rage", 3), ("atk", 6, 3)]),
    "敌怪7": lambda: E("敌怪7", 38, [("atk", 1, 4), ("drain", 9), ("atk", 3, 4)]),
    "精英1": lambda: E("精英1", 72, [("atk", 12, 1), ("str", 5), ("atk", 17, 1)]),
    "大树精": lambda: E("大树精", 162, [("entangle", 4), ("atk", 14, 1), ("str", 2), ("atk", 16, 1)]),
    # 三小只：企划书给的意图按三只分配，这里简化为固定循环
    "三小只A": lambda: E("三小只·11", 11, [("atk", 4, 1), ("str", 5), ("atk", 4, 1)]),
    "三小只B": lambda: E("三小只·16", 16, [("debuff", "缓慢"), ("atk", 11, 1)]),
    "三小只C": lambda: E("三小只·6", 6, [("atk", 4, 1), ("debuff", "缓慢")]),
}

# 楼层遭遇（地图 1 的切片：弱怪 → 强怪 → 精英 → Boss）
FLOORS = [
    ("入口·苔径", "敌怪1"),
    ("积水走廊", "敌怪2"),
    ("碎石阶", "敌怪3"),
    ("湿洞", "三小只"),
    ("巢穴外缘", "敌怪5"),
    ("精英·锈铁门", "精英1"),
    ("树心", "大树精"),
]

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
        self.draw_pile, self.hand, self.discard = [], [], []

    # —— 牌堆 ——
    def new_battle(self):
        self.draw_pile = list(self.deck)
        random.shuffle(self.draw_pile)
        self.hand, self.discard = [], []
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
    k = it[0]
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


# ---------------------------------------------------------------- 显示

def show_state(player, enemies, turn):
    print()
    print(hr())
    print(f"第 {turn} 回合 · 生命 {max(0, player.hp)}/{player.max_hp} "
          f"[{bar(max(0, player.hp), player.max_hp)}]")
    print(f"体力 {player.stamina}/{RUN_STAMINA} [{bar(player.stamina, RUN_STAMINA)}]"
          f" · 格挡 {player.block}")
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
            player.discard.append(name)
            for l in log:
                print("  " + l)
            log = []
            enemies[:] = [e for e in enemies if e["hp"] > 0]
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

    win = player.hp > 0
    if win:
        print(f"\n✔ 清空「{floor_name}」")
    return win


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
    print("  体力见底就回不了店了，省着点打。")
    print(hr("═"))
    input("回车开始 >> ")

    player = Player(STARTER_DECK)
    run_run(player)


def run_run(player, policy=None):
    """跑一整局。policy(player, enemies) -> 命令字符串；None 表示由玩家输入。"""
    loot = []
    cleared = 0
    for floor_name, wave in FLOORS:
        print("\n" + hr("═"))
        print(f"  ▶ {floor_name}   体力 {player.stamina}/{RUN_STAMINA}")
        print(hr("═"))
        if wave == "三小只":
            enemies = [ENEMIES["三小只A"](), ENEMIES["三小只B"](), ENEMIES["三小只C"]()]
        else:
            enemies = [ENEMIES[wave]()]
        ok = battle(player, enemies, floor_name, policy)
        if not ok:
            print("\n" + hr("═"))
            print("  ✘ 倒在了地牢里。")
            print("  带回的东西全丢了（原型规则：失败 = 全丢）。")
            print(hr("═"))
            return {"win": False, "cleared": cleared, "loot": [], "stamina": player.stamina}
        cleared += 1
        if floor_name.startswith("精英") or floor_name == "树心":
            loot.append(random.choice(LOOT_TABLE))
        loot.append(random.choice(LOOT_TABLE))
        player.hp = min(player.max_hp, player.hp + HEAL_AFTER_BATTLE)
        if wave != "大树精":
            card_reward(player, policy)
        if player.stamina <= 0:
            print("\n体力耗尽，只能回店了。")
            break

    print("\n" + hr("═"))
    print("  ✔ 回店结算")
    print(f"  剩余体力 {player.stamina}/{RUN_STAMINA}    生命 {max(0, player.hp)}/{player.max_hp}")
    print(f"  战利品：{'、'.join(loot) if loot else '空手而归'}")
    print(f"  卡组 {len(player.deck)} 张 · 推进 {cleared}/{len(FLOORS)} 层")
    print(hr("═"))
    print("  这些东西第二天营业能用（经营部分未实现）")
    return {"win": cleared == len(FLOORS), "cleared": cleared,
            "loot": loot, "stamina": player.stamina}


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n已中断。")
