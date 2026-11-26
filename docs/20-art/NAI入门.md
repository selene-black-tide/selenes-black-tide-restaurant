# NovelAI 二次元立绘 · 入门手册

> 基于 NovelAI 官方文档（2026-11 核对）+ 侧重点：游戏立绘，不是插画约稿
> 目标：从零到能出「角色一致、可交付、可商用」的立绘

---

## 0. 一句话：NAI 到底是什么

**它不是「你跟它描述一幅画」，而是「你在点菜」。**

普通生图 AI（Midjourney、GPT Image）吃自然语言："一个穿蓝色长袍的女巫站在花田里，夕阳"。
NovelAI 吃 **tag**（英文标签），一个词一个配料：`1girl, solo, witch hat, blue robe, flower field, sunset`。

原因：NAI 是用 Danbooru 那种图库的标签训练出来的，模型学到的是"标签→画面元素"的对应关系。所以**用 tag 喂它，控制力比自然语言强一个量级**。

代价：你得学一套词汇。这是唯一门槛，过了就通了。

---

## 1. 核心认知：一致性靠「堆细节」，不靠「写好提示词」

这是二次元立绘的全部秘密，官方教程原话的意思是：

> **服装描述得越细，跨图一致性越高。**

对比一下（官方示例）：

❌ 太笼统 → 每次出的衣服都不一样
```
1girl, solo, full body, witch hat, robe
```

✅ 细到每件单品都有颜色/材质 → 基本稳定
```
1girl, solo, full body,
swept bangs, bob cut, medium hair, platinum blonde hair, aqua eyes, pale skin,
witch hat, blue headwear, blue cape, white shirt, long sleeves,
corset, leather belt, leather pouch,
short skirt, blue skirt, frilled skirt, black pantyhose,
brown gloves, knee boots,
medium breasts, skinny, slim legs
```

**原理**：你不写的部分，AI 自由发挥。写得越少，每张图随机性越大。立绘要的是「同一个角色」，那就得把该锁的锁死。

---

## 2. Tag 语法三件套（必背）

| 写法 | 作用 | 例子 |
|---|---|---|
| `tag, tag, tag` | 逗号 + **空格**分隔 | `1girl, long hair, blue eyes` |
| `{tag}` | **加强**，括号越多越强 | `{{{messy hair}}}` 头发更乱 |
| `[tag]` | **削弱** | `[[[messy hair]]]` 头发低调一点 |

⚠️ 括号必须**左右数量一致**，除非在 prompt 最末尾。
⚠️ 加太多会出怪东西（画面畸形、颜色崩）。

### 顺序有影响

官方推荐的 tag 顺序：

```
1boy / 1girl → 角色 → 作品系列 → 其他随便
```

**越靠前的 tag 权重越高**（V3 及以下模型尤其明显）。所以：主体放前面，装饰放后面。

---

## 3. 立绘 prompt 的骨架（照这个填）

```
[主体] 1girl, solo
[构图] full body / cowboy shot / upper body
[头发] 长度 → 样式 → 颜色
[脸]   眼瞳色、皮肤
[服装] 头 → 上身 → 腰 → 下身 → 手 → 脚，每件都带颜色
[体型] 可选
```

**从官方的完整示例学结构：**

```
1girl, solo, full body,                              ← 主体 + 构图
swept bangs, bob cut, medium hair, platinum blonde hair,   ← 头发：样式→长度→颜色
aqua eyes, pale skin,                                ← 眼睛、皮肤
witch hat, blue headwear, blue cape, white shirt, long sleeves,  ← 上装
corset, leather belt, leather pouch,                 ← 腰
short skirt, blue skirt, frilled skirt, black pantyhose,  ← 下装
brown gloves, knee boots,                            ← 手、脚
medium breasts, skinny, slim legs                    ← 体型
```

### 各部位常用 tag 速查

**发型长度**：`very short hair` / `short hair` / `medium hair` / `long hair` / `very long hair` / `absurdly long hair`

**发型样式**：`bob cut` / `braid` / `ponytail` / `twintails` / `high ponytail` / `side ponytail` / `bangs` / `blunt bangs` / `sidelocks` / `ahoge`（呆毛）/ `curly hair` / `messy hair`

**发色**：`black hair` / `blonde hair` / `silver hair` / `blue hair` / `pink hair` / `purple hair` / `red hair` / `white hair` / `gradient hair` / `two-tone hair`

**瞳色**：`aqua eyes` / `blue eyes` / `green eyes` / `red eyes` / `golden eyes` / `purple eyes` / `heterochromia`（异色瞳）

**肤色**：`pale skin` / `tan` / `dark skin`

**构图（由近到远）**：`close-up` / `portrait` / `upper body` / `cowboy shot` / `full body` / `wide shot`

**视角**：`from side` / `from above` / `from below` / `from behind` / `facing viewer` / `dutch angle`

**游戏立绘专用（V5）**：`visual novel sprite` / `visual novel art` / `visual novel cg` / `character image`

**多视角设定图**：`multiple views` / `reference sheet` / `zoom layer`

---

## 4. 新手一定会困惑的三件事

### ① 画质词是「自动加的」，你没写也有

NovelAI 有个 **Quality Tags 开关，默认打开**。它会往你 prompt 末尾自动塞：

- V5 Full / Curated 轻量档：`very aesthetic, amazing quality, no text`
- 标准档：`very aesthetic, masterpiece, no text`

**关键**：这些词**不显示**在你的 prompt 里，但**占 context 空间**。

所以两条推论：
- 你疑惑「我没写 masterpiece 为什么画质还行」→ 就是它加的
- 你想完全手动控制风格 → 关掉这个开关，自己写

### ② 图不会自动保存，关掉页面全没

官方明确：**NovelAI 出于隐私不保存任何生成图**。刷新/关页面 = 全丢。

**必须做的**：满意的立刻点 Download。批量用 Download ZIP。

配套技巧：把图拖回网页，能**还原出当时的 prompt 和所有参数**。所以每张图本身就是你的存档。

### ③ seed 只锁「构图骨架」，不锁角色

新手最大误解：以为固定 seed 就能固定角色。

真相：同 seed 只保证「同一团初始噪声」，**你改 prompt 构图就变，角色也会飘**。

固定 seed 的正确用法：**做对照实验**。改一个 tag、seed 不变，就能看出这个 tag 到底干了什么。这是学 tag 最快的办法。

另外注意：把图拖回网页时 **seed 会一起导入**。想用同样的 prompt 出张不同的图，记得点一下 seed 值清空它。

---

## 5. Undesired Content（负向清单）

就是个「我不想要这些」的框。写什么都行，`{}` 和 `[]` 一样能用。

常用负面词：

```
lowres, bad anatomy, bad hands, extra fingers, fewer fingers,
watermark, signature, username, text, logo,
heterochromia（防止两只眼颜色不一）, 
```

**实用场景**：官方教程里往负面塞 `petals`，画面里的飞花瓣全没了。**AI 乱加什么，就把它塞这里**。

---

## 6. 第一课：三个练习（从照抄到自主）

按官方「用同一 seed 逐步改」的方法做，20 分钟能跑完。

### 练习 A｜照抄跑通（10 分钟）

把第 3 节那个「女巫」完整 prompt 直接贴进去，出 4 张。

**观察目标**：4 张里角色的衣服、发色、瞳色是不是基本一致？这就是「堆细节」的效果。

### 练习 B｜拆解 tag（10 分钟）

固定 seed 不动，依次做：

1. 把 `full body` 改成 `upper body` → 看构图怎么变
2. 在 `blue cape` 外面套 `{{{}}}` → 看斗篷怎么强化
3. 把 `platinum blonde hair` 改成 `[[[platinum blonde hair]]]` → 看发色怎么变淡

**观察目标**：建立「这个 tag 管这一块」的手感。这是所有后续技能的地基。

### 练习 C｜三个新手典型错误（直接给批改）

**① 漏了 `solo`**
- ❌ `1girl, long hair, blue eyes, full body`
- 错在哪：只说了 1girl，没说画面里只有她。AI 会在背景塞别的人或角色
- 正确：`1girl, solo, long hair, blue eyes, full body`

**② 写了自然语言**
- ❌ `一个穿黑裙子的银发少女，手持长剑，全身`
- 错在哪：NAI 训练数据是英文 tag，不是句子；中文句子它基本读不懂
- 正确：`1girl, solo, silver hair, black dress, holding sword, full body`

**③ 同一个 tag 又加强又削弱**
- ❌ `1girl, solo, silver hair, {{black dress}}, {{{black dress}}}, [[black dress]]`
- 错在哪：同一个元素给了三个方向相反的指令，模型只能瞎猜，结果不稳定
- 正确：只留一个方向，`1girl, solo, silver hair, {{{black dress}}}`

**记住这个规律**：AI 不会因为你说得多就更准，只会因为你说得**一致**才更准。

---

## 7. 进阶：两个一致性工具（第二阶段再学）

### Vibe Transfer（风格/画风迁移）

上传一张图当「灵感源」，让新图往它那边靠。

- **Reference Strength**：越接近 1 越像，太高会盖过你的文字 prompt
- 多个 vibe 的强度**加起来应 ≤ 1.0**（有 Normalize 开关可自动归一）
- 最多 **16 个 vibe**；超过 4 个，每个额外 +2 Anlas
- 编码一次收 **2 Anlas**（改 Information Extracted 要重新编码 = 再收钱）
- **省钱技巧**：编码后下载 `.naiv4vibe` 文件，以后导入不再扣编码费

### Precise Reference（精确参考）

比 Vibe Transfer 更硬地锁「角色/构图」。做立绘差分的主力。

---

## 8. 学习路线（别跳步）

| 阶段 | 目标 | 交付物 | 预计 |
|---|---|---|---|
| **0** | 跑通第一张 | 4 张能看的图 | 今天 |
| **1** | 掌握 tag 语言 | 能凭记忆写出角色的完整 tag 串 | 1~2 天 |
| **2** | 钉死一个角色 | 同一角色 3 个不同视角，肉眼认得是同一人 | 3~5 天 |
| **3** | 表情差分 | 基于定稿出 5 个表情 | 1 周 |
| **4** | 量产 | 1 个角色 10 张图，不返工 | 2 周 |

到了阶段 4 稳定了，就该考虑**转本地**（你的 5060 8GB 跑 Illustrious/NoobAI）—— 边际成本归零，且能训自己的 LoRA，那才是游戏项目的终局。

---

## 9. 立绘 QC 清单（交付前过一遍）

- [ ] 头身比符合项目规范
- [ ] 角色记忆点齐全（呆毛/耳饰/纹样位置）
- [ ] 手指数量正确（AI 重灾区）
- [ ] 两只眼颜色一致
- [ ] 与定稿标准像比对：配色、花纹位置没漂
- [ ] 无多余水印/文字
- [ ] 透明底边缘干净（如果用 transparent background）

---

## 参考

- [NovelAI 图像生成入门教程](https://docs.novelai.net/en/image/tutorial-imgintro)
- [Tagging 语法](https://docs.novelai.net/en/image/tags)
- [角色一致性教程](https://docs.novelai.net/en/image/tutorial-charactercreation)
- [Vibe Transfer](https://docs.novelai.net/en/image/vibetransfer) · [Precise Reference](https://docs.novelai.net/en/image/precisereference)
- [Quality Tags 开关](https://docs.novelai.net/en/image/qualitytags)
- [订阅与 Anlas 规则](https://docs.novelai.net/en/subscription)
- [服务条款（内容归你）](https://novelai.net/terms)
