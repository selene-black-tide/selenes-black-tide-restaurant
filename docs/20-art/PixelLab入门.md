---
title: PixelLab入门
status: 草稿
updated: 2026-11-26
owner: Mizuki
tags: [美术, 像素, AI工具]
---

# PixelLab 入门 · 图标与等距砖

> 信息基线：2026-11-26 官网 docs + API docs + B 站视频逐个核对
> 定位：**本项目的 PixelLab 只干两件事——UI/道具图标、等距餐厅砖**。角色原画走 [NAI入门.md](NAI入门.md)

---

## 0. 一句话

**PixelLab 是补位工具，不是主力。** 它的招牌功能（8 方向旋转、精灵动画）是给 RPG 走位角色用的，我们这游戏没有这个需求——经营是等距静态餐厅，肉鸽是卡牌对战、卡面是静态 CG。

所以学它只需要四个工具面：**图标、等距砖、原画降像素、inpaint 修图**。一周能上手。

---

## 1. 定位从哪来

[游戏理念.md](../../游戏理念.md) 第 2.10 段（2026-11-26 组长定）：

> 「NAI画原画，然后对着改像素」「简单的图标就直接用PixelLab」

第 3 节美术行落的也是这条。所以工具分工是：

| 要什么 | 用什么 | 产出放哪 |
|---|---|---|
| UI / 道具 / 食材图标 | **PixelLab** | `assets/ui/` |
| 等距餐厅砖、建筑 | **PixelLab** → Aseprite 精修 | `assets/demo/` |
| 角色 / 怪物 CG、卡面 | NAI → 对着改像素（Aseprite） | `assets/run/` |
| 图标以外的矢量、字体 | 不归 PixelLab 管 | — |

⚠️ **别指望 PixelLab 出二次元角色。** 它是「通用像素游戏味」，跟本项目的「高 hi-bit + 二次元」有硬落差。落差靠两样补：参考图锁风格 + Aseprite 手改。

---

## 2. 四个入口（按上手顺序选）

| 入口 | 在哪 | 适合 | 限制 |
|---|---|---|---|
| **Simple Web Creator** | `pixellab.ai/create` | **第一周就用这个** | 功能最少 |
| **Characters** | `pixellab.ai` 上的角色页 | 文字出 4/8 方向带动画角色 | 我们用不上（见第 0 节） |
| **Pixelorama**（浏览器编辑器） | 站内打开 | 要边生成边改 | 只支持桌面浏览器 |
| **Aseprite 扩展** | 本地 Aseprite | 长期主力工作流 | 见下方安装条件 |
| **MCP / API** | `api.pixellab.ai/mcp` | 批量出图、让我代跑 | 要 API key |

### Aseprite 扩展的硬条件

- **Aseprite ≥ v1.3.7**，**试用版不支持插件**
- 装法：账号页下载扩展 → 双击装；不行就 `Edit > Preferences > Extensions > Add Extension`
- 重启后允许它访问 `package.json` 和联网（websocket）
- 唤起：`Edit > PixelLab > Open plugin`，或 `Ctrl + Space + P`

### 接进 AI 助手（可选，省事）

```powershell
claude mcp add pixellab https://api.pixellab.ai/mcp -t http -H "Authorization: Bearer YOUR_KEY"
```

接上之后我可以直接按清单批量出图，你只负责验收。

---

## 3. 工具地图：学哪些、跳过哪些

底层两个模型：**PixFlux**（中到大图）、**BitForge**（小到中图）。

| 工具 | 用不用 | 说明 |
|---|---|---|
| `Create UI elements (Pro)` | **必学** | 血条、按钮、背包格、菜单，可出透明底 |
| `Create isometric tile` / `Create tileset` | **必学** | 等距砖，等距餐厅的地基 |
| `Image to pixel art` + `Reduce colors` + `Unzoom pixel art` | **必学** | NAI 原画 → 像素粗翻，省手改力气 |
| `Inpaint` / `Inpaint v3` | **必学** | 只改涂黑的部分，修手、改配色 |
| `Remove background` | 会用 | 抠透明底 |
| `Create image`（S-M / M-XL / S-L Pro） | 会用 | 通用出图，图标也能出 |
| `Create 8-directional sprite (Pro)` | **跳过** | 无走位角色需求 |
| `Animate with text` / `Animate with skeleton` | **跳过** | 同上 |
| `Create map` / `Extend map` | 暂缓 | 肉鸽地图是卡牌式节点图，不是瓦片地图 |
| `Try on` / `Transfer outfit` / `Re-pose` | 跳过 | 换装向，用不上 |

---

## 4. 四个工具的具体参数

### 4.1 图标：`Create UI elements (Pro)`

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

### 4.2 等距砖：`Create isometric tile`

| 参数 | 取值 | 怎么填 |
|---|---|---|
| `Isometric Tile Shape` | `Thick` / `Thin` / `Block` / `Reference` / `None` | **先挑一种定型，之后统一**；`Reference` 可挂参考图锁形状和明暗 |
| `Description` | 自然语言 | `grass on top of dirt`、`wooden floor`、`stone brick wall with moss` |
| `Outline` / `Shading` / `Details` | 各一个下拉 | **三张必须同一组设置**，这是统一风格的主要开关 |
| `Tile Size` | 16×16 / 32×32 | 17 官方 UI 只给这两档；要 48/64 得走 API |
| `Init Image` | 可选 | 越高越贴参考图，越低越自由 |
| `Guidance Weight`（Advanced） | 数值 | 越高越贴文字描述，同时影响描边/明暗/细节 |
| `Target palette`（Color） | 色板 | 全项目统一色数 |

⚠️ **和 API 的差别**：[像素等距工作流.md](像素等距工作流.md) 里那套 `tile_view_angle` / `elevation` / `tile_flat_top_px` / `style_copy` 是 **API 参数**，网页 UI 上没有。要按那份文档的参数做，必须走 API。

**本项目要钉死的三个值**（改之前进 `decisions/` 写 ADR）：

```
投影     isometric 2:1
光照     左上角来光（顶面 100% / 左墙 70% / 右墙 50%）
tile    32px（UI 能出的最大档）
```

### 4.3 原画降像素：`Image to pixel art` → `Reduce colors` → `Unzoom pixel art`

这是省力的那条路，替代「NAI 原画手改像素」。

```
NAI 原画 → Image to pixel art（粗翻）
        → Reduce colors（压到项目色板色数）
        → Unzoom pixel art（对齐真实像素网格，治「假像素」）
        → Aseprite 手修（阴影方向、边缘、细节）
```

**一定要跑 `Unzoom`**，跳过的话放大到全屏一眼假：边缘毛、色数飘。

### 4.4 修图：`Inpaint`

- 在生成图上开一个新图层，**把要改的地方涂黑**——模型只会改黑色部分
- 把当前图设为 init image，调低 `Init image strength`（给模型更多自由）
- `Output method` 选 `Modify current layer`，改完直接落回原图
- 可以反复迭代，直到满意

典型用途：AI 的手永远画不好 → 涂黑重出；图标配色不对 → 涂黑换色。

---

## 5. 七天路线

| 天 | 干什么 | 验收 |
|---|---|---|
| 1 | 注册免费档（不用信用卡），跑通第一张 `Create image` | 真出了一张图 |
| 2–3 | 只做图标，凑 10 个，全走 `Create UI elements (Pro)` + 透明底 | `assets/ui/` 有 10 张 32–64px 图标 |
| 4 | 定 tile 尺寸和光照，出「标准建筑」1 栋（8~16 候选里挑 1） | 顶面/左墙/右墙亮度对比清晰、光从左上 |
| 5 | 批量出等距砖，全带同一组 `Outline/Shading/Details` | 4 角地表 tile + 3 栋同风格建筑 |
| 6 | 拿一张 NAI 原画跑「降像素」三段，跟手改比用时 | 出一版粗翻稿，记下省了多少时间 |
| 7 | 回头看：哪一步出的东西离不开 Aseprite？多就调整路线 | 一页笔记，决定长期入口（网页 / Aseprite 扩展 / API） |

**验收标准不是「图好看」，是「能进游戏不返工」。**

---

## 6. B 站教程（2026-11-26 逐个核对时长和播放量）

### 必看（3 个）

| 视频 | UP | 时长 | 数据 | 为什么 |
|---|---|---|---|---|
| [【PixelLab教程】个人像素游戏开发者的神器！](https://www.bilibili.com/video/av115899860322796) | 135itsuki | 54m20s | 13.7w 播放 / 1130 收藏 | **全站唯一正经讲 pixellab.ai 的长教程**，简介直接写 pixellab.ai，2026-01 出 |
| [一键生成像素动画｜PixelLab 新工具实操全攻略与 AI 提示词技巧](https://www.bilibili.com/video/av116275753781319) | ChyiZ_ | 6m56s | 1.2w 播放 / 998 收藏 | 短平快，官方 `Animate with text` 的中文实操；学动画那天的第一站 |
| [Aseprite 二十分钟快速上手](https://www.bilibili.com/video/av99496436) | 石西籽 | 19m17s | 56.7w 播放 | Aseprite 是最终精修场地，先用 20 分钟把软件熟掉 |

### 选看（3 个）

| 视频 | UP | 时长 | 什么情况下看 |
|---|---|---|---|
| [【唐老狮直播】用 AI 生成游戏 2D 美术资源（PixelLab）](https://www.bilibili.com/video/av116685218514112) | 一唐老狮一 | 47m52s | 想看「整包资产怎么排」的实战视角 |
| [Nine 浅聊像素画/新手向：如何确定画布尺寸？](https://www.bilibili.com/video/av684371290) | Nine叔 | 8m54s | 定 32px 之前看，跟第 4.2 节直接相关 |
| [【中配】PixelLab 教程：GBA 风格精灵动画](https://www.bilibili.com/video/av116560245036769) | 像素博物馆 | 12m40s | 官方 YouTube 中配搬运，只在要做像素小角色时看 |

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
4. 动画那部分**这个阶段完全不看**（见第 0 节）

---

## 7. 官方材料（中文不够时查这里）

**教程视频 12 个**，按需挑（我们只要前三个）：

- [Generate Tilesets](https://youtu.be/sE1s5ZYfxqk) — 等距砖，第 4 天看
- [Create an RPG UI Set](https://youtu.be/BdoUMKhZ1Ys) — 图标成套，第 2 天看
- [Inpainting in Aseprite & PixelLab Editor](https://youtu.be/9eAlZlQmZBg) — 修图，随时
- [Build a Game with MCP + API](https://youtu.be/fvPmuk-usgw) — 要批量时看
- 其余 8 个是动画 / 角色 / 地图向，暂不看

**文档页**（按需查，别通读）：

- 入门实操：<https://www.pixellab.ai/docs/getting-started>（标题叫入门，内容是 init image + inpaint 全流程，全站最像教程的一页）
- 使用入口：<https://www.pixellab.ai/docs/ways-to-use-pixellab>
- Aseprite 扩展安装：<https://www.pixellab.ai/docs/installation>
- 图标工具：<https://www.pixellab.ai/docs/tools/create-ui-elements-pro>
- 等距砖：<https://www.pixellab.ai/docs/tools/create-isometric-tile>
- API / MCP：<https://api.pixellab.ai/mcp/docs>

---

## 8. 四个坑

1. **文档别通读。** 全站 71 页，`old` / `new` / `Pro` 三代工具同时挂着，官方自己没清干净，顺着读会撞一堆「这个已弃用」。
2. **额度别乱烧。** UI elements 按尺寸扣 10~25 次 generation，512px 一次 25 次。练手固定小尺寸，定稿再放大。
3. **画风落差靠两样补。** 参考图（`Reference` / `Concept Image` / `Init Image`）+ 固定的 `Outline/Shading/Details` 组合，剩下靠 Aseprite。别指望提示词解决问题。
4. **免费档、商用条款先看清。** 「免费」和「可商用」是两件事，见 [AI美术选型.md](AI美术选型.md) 第五节。

---

## 9. QC 清单（每 10 张抽检）

- [ ] 色数没超项目色板
- [ ] 放大 8 倍看，边缘是硬方块，不是糊的（没跑 `Unzoom` 的典型症状）
- [ ] 等距砖：光从左上、左墙比右墙亮、亮度差不小于 25%
- [ ] 同一批图标，描边粗细一致、高光位置一致
- [ ] 透明底边缘干净，没有白边
- [ ] 素材尺寸跟 `assets/` 里的现有资产对得上，没有混用 32 / 64

---

## 10. 待定

- [ ] **餐厅里要不要走动的角色**（服务员 / 客人）。要 → 得学 `Create 8-directional sprite` 和动画；不要 → 第 0 节的判断成立。这条 [游戏理念.md](../../游戏理念.md) 没写，属未定。
- [ ] **tile 用 32 还是 64**。32 是网页 UI 能出的最大档，64 必须走 API。定了才能批量。
- [ ] **免费档额度到底多少**。站内文档写「Free：40 次快速 + 5 次/天」，官网首页只写「不用信用卡」，实际以注册后结算页为准。

---

## 相关

- [游戏理念.md](../../游戏理念.md) · [AI美术选型.md](AI美术选型.md) · [NAI入门.md](NAI入门.md) · [像素等距工作流.md](像素等距工作流.md) · [INDEX.md](../../INDEX.md)
