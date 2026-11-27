# Selene's Black Tide Restaurant

**塞勒涅的黑潮餐馆** · 奇幻餐馆模拟经营 × 卡牌肉鸽

> 白天接待人类，午夜招待非人类。荤的下地牢打，素的靠自己种。
> 经营是主体，肉鸽只是「高方差的搞钱方式」。

---

## 这是什么

游戏开发部的协作仓库。设计文档、美术流程、代码、决策记录全在这里，组员共用。

| | |
|---|---|
| **仓库** | https://github.com/selene-black-tide/selenes-black-tide-restaurant |
| **组织** | [selene-black-tide](https://github.com/selene-black-tide)（Free 版） |
| **可见性** | 公开——组员和各家 AI 都能直接读，不用配 token |

组员用的 AI 不一样（目前主要是 **DeepSeek** 和 **Claude**），所以仓库里有一套统一规矩——**给 AI 干活之前，先把 [AGENTS.md](AGENTS.md) 丢给它**。换成 GPT 或 Gemini 也一样吃得下。

---

## 第一次来？四条命令

```powershell
# 1. 克隆
git clone https://github.com/selene-black-tide/selenes-black-tide-restaurant.git

# 2. 中文文件名不乱码（不加这个，git status 里全是 \346\270\270）
git config --global core.quotepath false

# 3. 设你自己的提交身份（都叫同一个名字的话，出了事分不清谁改的）
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"

# 4. 拉最新，别在旧版本上改
git pull
```

然后按顺序读：**本文件** → [游戏企划书.md](docs/00-overview/游戏企划书.md) → [游戏理念.md](游戏理念.md) → [CONTRIBUTING.md](CONTRIBUTING.md)。半小时能接上。

> 不想敲命令？装个 **GitHub Desktop**，`File → Clone repository` 选这个仓库，上面四步里除了第 2 步它会问，其余都自动。

---

## ★ 最重要的一份：游戏企划书

**[docs/00-overview/游戏企划书.docx](docs/00-overview/游戏企划书.docx)**

| | |
|---|---|
| **地位** | 项目**正式定稿**，一切设计的最高依据 |
| **冲突** | 任何文档和它矛盾时，**以它为准** |
| **谁维护** | Mizuki。**AI 不要直接改这个文件**（二进制，改了没人 review 得出来） |
| **给 AI 读** | [游戏企划书.md](docs/00-overview/游戏企划书.md) —— 从 docx 自动导出的镜像，**改内容改 docx，不要手改这份 md** |
| **和 `游戏理念.md` 的分工** | 企划书 = 定稿的结论；`游戏理念.md` = 每天归档群聊的活文档，记细节、记讨论、记待拍板 |

---

## 改完 Word 之后：一条命令发布

企划书源文件是 `docs/00-overview/游戏企划书.docx`，但它**不能直接给人看**——GitHub 不渲染 Word，别人点开只能下载。真正给别人看的是同目录的 `游戏企划书.md`。

所以每次改完：

1. 编辑 `docs/00-overview/游戏企划书.docx`，存盘
2. 双击桌面上的 **「发布游戏企划书」**，或者在仓库根目录跑：

```powershell
python tools/publish_plan.py
```

它做四件事：导出 md → 暂存 → 提交 → 推送。

> **看到「没有任何改动，跳过提交」就说明你的存盘没落到本地文件。**
> WPS 默认往云文档存，这时候回 Word 里点「另存为」，手动选到 `docs\00-overview\` 覆盖一次。

---

## 30 秒找到你要的东西

| 你现在要 | 打开 |
|---|---|
| **★ 看最权威的那份** | **[游戏企划书.docx](docs/00-overview/游戏企划书.docx)** ← 正式定稿，最高依据 |
| 知道设计细节、还没定什么 | [游戏理念.md](游戏理念.md) ← 活文档，每天 22:00 归档群聊 |
| 找某份具体文档 | [INDEX.md](INDEX.md) ← 全库索引 |
| 让 AI 帮你干活 | [AGENTS.md](AGENTS.md) ← 只丢这一个文件就够 |
| 怎么提交、提交信息怎么写 | [CONTRIBUTING.md](CONTRIBUTING.md) |
| 某个设定为什么当初这么定 | [decisions/](decisions/) ← 决策记录 ADR |
| 发企划书给别人看 | 上面那节「一条命令发布」 |

---

## 目录地图

```
.
├── README.md              ← 你在这
├── AGENTS.md              ← 所有 AI 的统一入口（硬规则 R1–R9 + 术语表）
├── CONTRIBUTING.md        ← 人和 AI 的协作规范
├── INDEX.md               ← 全库文档索引，新增文档必须登记
├── 游戏理念.md            ← 活文档（设计细节 / 讨论记录 / 待拍板），每日 22:00 自动追加
│
├── docs/                  正式文档
│   ├── 00-overview/       企划书（docx 源 + md 镜像）
│   ├── 10-design/         系统设计、数值、关卡、剧情
│   ├── 20-art/            美术流程、AI 工具选型、资产规范
│   ├── 30-tech/           技术方案、引擎选型、接口约定
│   └── 90-archive/        废案、过期文档（不删，挪这来）
│
├── decisions/             决策记录 ADR 0001–0004：为什么这么定
├── tools/                 脚本：export_plan.py 导出企划书 / publish_plan.py 一键发布
├── assets/                美术与音频资源（大文件走 Git LFS）
│   └── demo/              经营部分（等距）
├── src/                   代码（还没建，第一份代码提交时自动出现）
│
├── Mizuki-77/             个人工作区（Mizuki）
├── alvinczq7-cell/        个人工作区（Alvin）
├── Ng.j.d/                个人工作区（Ng.j.d）
└── Shadorange/            个人工作区（Shadorange）
```

> 个人目录里放的是**草稿**，不算项目结论，也不用登记 `INDEX.md`。四个目录各自的 README 写了规矩。

---

## 三条铁律

1. **先看企划书，再看活文档。** 设计上有疑问，先看 [游戏企划书](docs/00-overview/游戏企划书.docx)；它没写的，看 [游戏理念.md](游戏理念.md) 的「待拍板」；两边都没有，就是**还没定**，别自己补。
2. **新增文档必须登记进 `INDEX.md`。** 不登记等于没写——别人和 AI 都找不到。
3. **术语用 `AGENTS.md` 第 6 节的英文 key。** 别各写各的，`风评` / `reputation` / `rating` 混着来，各家 AI 会各翻译各的。

---

## 组员

| 谁 | GitHub | 分管 | 常用 AI |
|---|---|---|---|
| Mizuki | [`Mizuki-77`](https://github.com/Mizuki-77) | 制作 / 企划 / 经营系统 / 美术 | DeepSeek |
| 橙子 | [`Shadorange`](https://github.com/Shadorange) | 卡牌肉鸽 / 数值 | DeepSeek |
| Alvin | [`alvinczq7-cell`](https://github.com/alvinczq7-cell) | 美术 / 交互与 UI / 基础代码 | Claude |
| Ng.j.d | [`WJD10086`](https://github.com/WJD10086) | 基础代码开发 / Debug / 交互设计 | DeepSeek |
| azike67 | [`azike67`](https://github.com/azike67) | _待本人填_ | _待本人填_ |

> 新组员加进来，先读 [README](README.md) → [游戏企划书.md](docs/00-overview/游戏企划书.md) → [游戏理念.md](游戏理念.md) → [CONTRIBUTING.md](CONTRIBUTING.md)，半小时能接上。
> 加入方式：组长在组织里发邀请 → 接受后成为成员，然后照上面「四条命令」拉仓库。

---

## 状态

- **阶段**：设计期（还没有可运行的原型）
- **体量红线**：大学四年内做完，超了直接砍
- **待拍板**：[游戏理念.md](游戏理念.md) 第 5 节共 **12 条**，动之前先问人
- **当前真瓶颈**：美术开不了工——[Alvin 的规范待决问题](alvinczq7-cell/art-prep/美术规范待决问题.md) 里第一批（分辨率 / 砖块尺寸 / 原画改像素的做法 / 色板）不拍板，出图没法定规格

---

## 版权

本项目版权归「游戏开发部」全体组员所有（**All Rights Reserved**）。

未经作者书面许可，不得用于商业用途、不得二次分发、不得当作公开素材库使用。

> 想换成 MIT / CC-BY 这类开放许可，先跟组长说一声——这会影响所有人对自己作品的权利。

## 欢迎提意见

设计讨论在 QQ 群「游戏开发部」。仓库里发现文档写错了、或者哪条规矩不合理，直接开 issue 或者在群里说，别自己闷头改。
