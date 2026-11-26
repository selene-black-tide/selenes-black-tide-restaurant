---
title: PixelLab入门
status: 草稿
updated: 2026-11-26
owner: Mizuki
tags: [美术, 像素, AI工具]
---

# PixelLab 入门 · 图标与等距砖

> 信息基线：2026-11-26 官网 docs + API docs + B 站视频逐个核对
> 定位：**图标、等距砖、场景小 sprite 用 PixelLab**；卡面 / 立绘走 [NAI入门.md](NAI入门.md)

---

## 0. 一句话

**PixelLab 管「小而多」的资产：图标、等距砖、餐厅里走动的小角色。** 角色立绘和卡面归 NAI 那条路。

第一周只学四个工具面（图标、等距砖、原画降像素、inpaint），**8 方向旋转和动画放第二阶段**——那是 PixelLab 最吃额度的功能，等砖和图标能稳定出图了再碰。

---

## 1. 定位从哪来

[游戏理念.md](../../游戏理念.md) 第 2.10 段（2026-11-26 组长定）：「NAI画原画，然后对着改像素」「简单的图标就直接用PixelLab」。

2026-11-26 追加：**餐厅里要有走动的角色**（服务员 / 客人），所以 PixelLab 多了一项活。

| 要什么 | 用什么 | 产出放哪 | 尺寸量级 |
|---|---|---|---|
| UI / 道具 / 食材图标 | **PixelLab** | `assets/ui/` | 32–64 |
| 等距餐厅砖、建筑 | **PixelLab** → Aseprite 精修 | `assets/demo/` | tile 32 |
| 餐厅里走动的小角色 | **PixelLab**（8 方向 + 动画） | `assets/demo/` | 高 48–64 |
| 角色立绘 / 卡面 CG | NAI → 对着改像素（Aseprite） | `assets/run/` | 高 400 左右 |
| 矢量、字体 | 不归 PixelLab 管 | — | — |

⚠️ **别指望 PixelLab 出二次元立绘。** 它是「通用像素游戏味」，跟本项目的「高 hi-bit + 二次元」有硬落差。落差靠两样补：参考图锁风格 + Aseprite 手改。

---

## 2. 四个入口（按上手顺序选）

| 入口 | 在哪 | 适合 | 限制 |
|---|---|---|---|
| **Simple Web Creator** | `pixellab.ai/create` | **第一周就用这个** | 功能最少 |
| **Characters** | `pixellab.ai` 上的角色页 | 文字出 4/8 方向带动画角色 | **第二阶段**：用它出场景 sprite |
| **Pixelorama**（浏览器编辑器） | 站内打开 | 要边生成边改 | 只支持桌面浏览器 |
| **Aseprite 扩展** | 本地 Aseprite | 长期主力工作流 | 见下方安装条件 |
| **MCP / API** | `api.pixellab.ai/mcp` | 批量出图、让 AI 代跑 | 要 API key |

### Aseprite 扩展的硬条件

- **Aseprite ≥ v1.3.7**，**试用版不支持插件**
- 装法：账号页下载扩展 → 双击装；不行就 `Edit > Preferences > Extensions > Add Extension`
- 重启后允许它访问 `package.json` 和联网（websocket）
- 唤起：`Edit > PixelLab > Open plugin`，或 `Ctrl + Space + P`

### 接进 AI 助手（可选，省事）

```powershell
claude mcp add pixellab https://api.pixellab.ai/mcp -t http -H "Authorization: Bearer YOUR_KEY"
```

接上之后可以按清单批量出图，人只负责验收。

---

## 3. 工具地图：学哪些、跳过哪些

底层两个模型：**PixFlux**（中到大图）、**BitForge**（小到中图）。

| 工具 | 用不用 | 说明 |
|---|---|---|
| `Create UI elements (Pro)` | **第一阶段** | 血条、按钮、背包格、菜单，可出透明底 |
| `Create isometric tile` / `Create tileset` | **第一阶段** | 等距砖，等距餐厅的地基 |
| `Image to pixel art` + `Reduce colors` + `Unzoom pixel art` | **第一阶段** | NAI 原画 → 像素粗翻，省手改力气 |
| `Inpaint` / `Inpaint v3` | **第一阶段** | 只改涂黑的部分，修手、改配色 |
| `Remove background` | 会用 | 抠透明底 |
| `Create image`（S-M / M-XL / S-L Pro） | 会用 | 通用出图，图标也能出 |
| `Create 8-directional sprite (Pro)` | **第二阶段** | 场景走动角色；一个角色 × 8 方向很吃额度 |
| `Animate with text` / `Animate with skeleton` | **第二阶段** | 先用 1 个角色试一帧，记下用时再决定给几个角色做 |
| `Create map` / `Extend map` | 暂缓 | 肉鸽地图是卡牌式节点图，不是瓦片地图 |
| `Try on` / `Transfer outfit` / `Re-pose` | 跳过 | 换装向，用不上 |

---

## 4. 先分清三层尺寸（别混）

这三层是三个独立的数，混了就会「以为会糊」或者「做出比例崩的画面」。

| 层 | 是什么 | 本项目取值 | 凭什么定的 |
|---|---|---|---|
| **tile** | 一块地砖多少像素 | **32**（等距 32×16 菱形） | 2026-11-26 定；网格最小单位 |
| **场景 sprite** | 餐厅里走动的小人 | 高 48–64 | 比 tile 高一档，站上去比例才正常 |
| **立绘 / 卡面** | 对话、卡牌上的人物 | 高 400 左右 | 独立于前两层，用高分辨率单独画 |

**为什么会「糊」**：不是 32 这个数字小，是**缩放不是整数倍**。素材按 1:1 画好，显示时按 2×、3×、4× 放大，边缘是硬方块；按 1.37× 放大就糊。

所以真正要先定的是**游戏基准分辨率**（内部渲染尺寸）：定 640×360，1080p 就是 3 倍整数放大；定 960×540 就是 2 倍。这个数定了，tile 32 和屏幕上一屏能看到多少格才算得出来。

> 待定：基准分辨率 640×360 还是 960×540。见第 11 节。

### 关于「高密度像素二次元」这种画风

参考图（477×653，Aseprite 里 1:1 截的）实测：**相邻像素 63% 都不同**，真实色数几百量级（两万多色里大半是 JPEG 噪声）。

意思是：**它不是手工一格一格点的 16 色像素画，是插画降像素。** 这类画风（也叫 hi-res pixel art / 伪像素）的实现路：

```
NAI 出原画 → Image to pixel art（降像素）
           → Reduce colors（压到项目色板）
           → Unzoom pixel art（对齐真实网格）
           → Aseprite 手修（阴影、边缘、发丝）
```

⚠️ 这条路的代价：**一致性差、色数会炸**。做 1 张很惊艳，做 140 张卡面会每张网格不对齐、颜色各走各的。所以必须先定色板，且每张都压色。

---

## 5. 四个工具的具体参数

### 5.1 图标：`Create UI elements (Pro)`

**参数**（只有四个，很简单）：

- `Description`：要什么，比如 `health bar` / `inventory slot` / `medieval stone button`
- `No Background`：**勾上**，直接出透明底
- `Color Palette`（可选）：写色系，比如 `blue and silver` / `brown and gold`
- `Concept Image`（可选）：拿一张已定稿的图标当风格参考
- `Seed`：锁复现

**额度消耗**（官方表，按尺寸跳档）：

| 尺寸 | generation |
|---|---|
| ≤32px | 10 |
| 33–42px | 15 |
| 43–64px | 10 |
| 65–85px | 15 |
| 86–128px | 10 |
| 129–170px | 15 |
| 171–256px | 10 |
| 257–341px | 15 |
| 342–512px | 25 |

**上限 512×512。** 可用位置：Aseprite、Pixelorama、Simple Creator。

练手固定 **32–64px**（10 次/张），定稿再放大。

### 5.2 等距砖：`Create isometric tile`

| 参数 | 取值 | 怎么填 |
|---|---|---|
| `Isometric Tile Shape` | `Thick` / `Thin` / `Block` / `Reference` / `None` | **先挑一种定型，之后统一**；`Reference` 可挂参考图锁形状和明暗 |
| `Description` | 自然语言 | `grass on top of dirt`、`wooden floor`、`stone brick wall with moss` |
| `Outline` / `Shading` / `Details` | 各一个下拉 | **三张必须同一组设置**，这是统一风格的主要开关 |
| `Tile Size` | 16×16 / 32×32 | 17 官方 UI 只给这两档；48/64 得走 API |
| `Init Image` | 可选 | 越高越贴参考图，越低越自由 |
| `Guidance Weight`（Advanced） | 数值 | 越高越贴文字描述，同时影响描边/明暗/细节 |
| `Target palette`（Color） | 色板 | 全项目统一色数 |

⚠️ **和 API 的差别**：[像素等距工作流.md](像素等距工作流.md) 里那套 `tile_view_angle` / `elevation` / `tile_flat_top_px` / `style_copy` 是 **API 参数**，网页 UI 上没有。要按那份文档的参数做，必须走 API。

**本项目已钉死**（2026-11-26，改之前进 `decisions/` 写 ADR）：

```
投影     isometric 2:1
光照     左上角来光（顶面 100% / 左墙 70% / 右墙 50%）
tile    32px（UI 最大档，也是等距 2:1 的标准档）
```

### 5.3 原画降像素：`Image to pixel art` → `Reduce colors` → `Unzoom pixel art`

见第 4 节末尾那段流程。**一定要跑 `Unzoom`**，跳过的话放大到全屏一眼假：边缘毛、色数飘。

### 5.4 修图：`Inpaint`

- 在生成图上开一个新图层，**把要改的地方涂黑**——模型只会改黑色部分
- 把当前图设为 init image，调低 `Init image strength`（给模型更多自由）
- `Output method` 选 `Modify current layer`，改完直接落回原图
- 可以反复迭代，直到满意

典型用途：AI 的手永远画不好 → 涂黑重出；图标配色不对 → 涂黑换色。

---

## 6. 路线

### 第一周（只做图标和砖）

| 天 | 干什么 | 验收 |
|---|---|---|
| 1 | 注册免费档（不用信用卡），跑通第一张 `Create image` | 真出了一张图 |
| 2–3 | 只做图标，凑 10 个，全走 `Create UI elements (Pro)` + 透明底 | `assets/ui/` 有 10 张 32–64px 图标 |
| 4 | 出「标准建筑」1 栋（8~16 候选里挑 1） | 顶面/左墙/右墙亮度对比清晰、光从左上 |
| 5 | 批量出等距砖，全带同一组 `Outline/Shading/Details` | 4 角地表 tile + 3 栋同风格建筑 |
| 6 | 拿一张 NAI 原画跑「降像素」三段，跟手改比用时 | 出一版粗翻稿，记下省了多少时间 |
| 7 | 回头看：哪一步离不开 Aseprite？ | 一页笔记，决定长期入口 |

### 第二周（才碰动画）

1. 挑 **1 个**必需角色（服务员或厨师长）
2. `Create 8-directional sprite (Pro)` 出 8 方向
3. `Animate with text` 出走路 / 待机
4. **计时**：一个角色的 8 方向 + 2 组动画，总共花多少小时
5. 拿这个数乘「要动的角色数」，再决定给几个角色做 —— 一个角色 8 方向 × 走/跑/待机 = 24 组帧，30 只怪物全做会直接冲破体量红线

**验收标准不是「图好看」，是「能进游戏不返工」。**

---

## 7. B 站教程（2026-11-26 逐个核对时长和播放量）

### 必看（4 个）

| 视频 | UP | 时长 | 数据 | 为什么 |
|---|---|---|---|---|
| [【PixelLab教程】个人像素游戏开发者的神器！](https://www.bilibili.com/video/av115899860322796) | 135itsuki | 54m20s | 13.7w 播放 / 1130 收藏 | **全站唯一正经讲 pixellab.ai 的长教程**，简介直接写 pixellab.ai，2026-01 出 |
| [一键生成像素动画｜PixelLab 新工具实操全攻略与 AI 提示词技巧](https://www.bilibili.com/video/av116275753781319) | ChyiZ_ | 6m56s | 1.2w 播放 / 998 收藏 | 官方 `Animate with text` 的中文实操；第二周再看 |
| [Aseprite 二十分钟快速上手](https://www.bilibili.com/video/av99496436) | 石西籽 | 19m17s | 56.7w 播放 | Aseprite 是最终精修场地，先花 20 分钟熟软件 |
| [【中配】PixelLab 教程：GBA 风格精灵动画](https://www.bilibili.com/video/av116560245036769) | 像素博物馆 | 12m40s | 1257 播放 | 官方 YouTube 中配搬运，做场景小 sprite 时最直接 |

### 选看（2 个）

| 视频 | UP | 时长 | 什么情况下看 |
|---|---|---|---|
| [【唐老狮直播】用 AI 生成游戏 2D 美术资源（PixelLab）](https://www.bilibili.com/video/av116685218514112) | 一唐老狮一 | 47m52s | 想看「整包资产怎么排」的实战视角 |
| [Nine 浅聊像素画/新手向：如何确定画布尺寸？](https://www.bilibili.com/video/av684371290) | Nine叔 | 8m54s | 定基准分辨率之前看，跟第 4 节直接相关 |

### 别踩这几个（同名 / 别的工具）

- [PixelLab使用教程](https://www.bilibili.com/video/av30861671)：2018 年、51 秒，是**同名的老手机修图 App**，不是 pixellab.ai
- [一键变成完美像素](https://www.bilibili.com/video/av115880818119877)：完美像素是另一款网页工具（perfectPixel）
- [AI 图一键转像素画](https://www.bilibili.com/video/av117162295433910)：自制算法，不是 PixelLab
- [Rika AI 像素动画](https://www.bilibili.com/video/av116094928950907)：竞品，别混进来

### 怎么看（重要）

**别一口气看完 54 分钟。** 正确姿势：

1. 先看主教程前 20 分钟（界面 + 基础生成）
2. 立刻上手做 3 个图标
3. 卡住了再回去查对应章节
4. 动画章节**第一周完全不看**

---

## 8. 官方材料（中文不够时查这里）

**教程视频 12 个**，按需挑：

- [Generate Tilesets](https://youtu.be/sE1s5ZYfxqk) — 等距砖
- [Create an RPG UI Set](https://youtu.be/BdoUMKhZ1Ys) — 图标成套
- [Inpainting in Aseprite & PixelLab Editor](https://youtu.be/9eAlZlQmZBg) — 修图
- [Build a Game with MCP + API](https://youtu.be/fvPmuk-usgw) — 要批量时看
- 其余 8 个是动画 / 角色 / 地图向

**文档页**（按需查，别通读）：

- 入门实操：<https://www.pixellab.ai/docs/getting-started>（标题叫入门，内容是 init image + inpaint 全流程，全站最像教程的一页）
- 使用入口：<https://www.pixellab.ai/docs/ways-to-use-pixellab>
- Aseprite 扩展安装：<https://www.pixellab.ai/docs/installation>
- 图标工具：<https://www.pixellab.ai/docs/tools/create-ui-elements-pro>
- 等距砖：<https://www.pixellab.ai/docs/tools/create-isometric-tile>
- API / MCP：<https://api.pixellab.ai/mcp/docs>

---

## 9. 四个坑

1. **文档别通读。** 全站 71 页，`old` / `new` / `Pro` 三代工具同时挂着，官方自己没清干净，顺着读会撞一堆「这个已弃用」。
2. **额度别乱烧。** UI elements 按尺寸扣 10~25 次 generation，512px 一次 25 次。练手固定小尺寸，定稿再放大。
3. **画风落差靠两样补。** 参考图（`Reference` / `Concept Image` / `Init Image`）+ 固定的 `Outline/Shading/Details` 组合，剩下靠 Aseprite。别指望提示词解决问题。
4. **免费档、商用条款先看清。** 「免费」和「可商用」是两件事，见 [AI美术选型.md](AI美术选型.md) 第五节。

---

## 10. QC 清单（每 10 张抽检）

- [ ] 色数没超项目色板
- [ ] 放大 8 倍看，边缘是硬方块，不是糊的（没跑 `Unzoom` 的典型症状）
- [ ] 等距砖：光从左上、左墙比右墙亮、亮度差不小于 25%
- [ ] 同一批图标，描边粗细一致、高光位置一致
- [ ] 透明底边缘干净，没有白边
- [ ] 场景 sprite 站在 tile 上比例正常（脚底对齐格子中心，不是浮空）
- [ ] 尺寸没混用：tile 32 / sprite 48–64 / 立绘 ~400，三层各走各的

---

## 11. 待定

- [ ] **基准分辨率**：640×360（1080p 3 倍）还是 960×540（2 倍）。这个数决定「一屏能看到几格 tile」，也决定立绘该画多大。**不糊的前提，先定这个。**
- [ ] **立绘/卡面的具体尺寸**：参考图是 477×653，可以按 400 高画，但要看基准分辨率能不能整数倍塞进去。
- [ ] **免费档额度到底多少**。站内文档写「Free：40 次快速 + 5 次/天」，官网首页只写「不用信用卡」，实际以注册后结算页为准。
- [ ] **色板**：还没定。「高密度像素二次元」这条路如果不定色板，140 张卡面会各走各的。

---

## 相关

- [游戏理念.md](../../游戏理念.md) · [AI美术选型.md](AI美术选型.md) · [NAI入门.md](NAI入门.md) · [像素等距工作流.md](像素等距工作流.md) · [INDEX.md](../../INDEX.md)
