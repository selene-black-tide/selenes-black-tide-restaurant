# 游戏 AI 美术选型建议

> 信息基线：2026-09《AI 游戏美术手册》+ 2026-11-25 联网核对
> 价格以官网为准，订阅前务必点开条款页

---

## 一句话结论

**不存在「最好的生图 AI」，只有「按格子配刀」。**

你们缺的不是「一个会画画的 AI」，是三把不同的刀：

| 要的东西 | 配哪把刀 | 一句话理由 |
|---|---|---|
| **图标 / UI / Logo** | **Recraft V4** | 唯一成熟的真 SVG 矢量输出，一次出一整套同风格图标，能改色、能进引擎、不失真 |
| **角色立绘 / 概念图** | 二次元 → **Niji 8**；写实/风格化 → **Midjourney V8.2** | Niji 8 是 2026-11-24 刚上的动漫模型，自带 edit model 做角色一致性 |
| **一致性 / 量产 50 张以上** | **LoRA**（本地 ComfyUI 或 Scenario/LiblibAI） | 垫图撑不住量，第 50 张一定漂移 |

---

## 二、先认清：AI 美术真正的瓶颈不在第一张图

**第一张图谁都能出。难的是第 50 张还像同一个游戏。**

一致性分四层，难度递增：

| 层次 | 问题 | 解法 |
|---|---|---|
| ① 画风一致 | 每张笔触/配色不统一 | 固定 STYLE 前缀（零成本，必做） |
| ② 角色身份一致 | 同一角色不像同一只 | 标准像垫图 / 指令编辑 / 多参考融合 / 角色 LoRA |
| ③ 多视角一致 | 三视图不像同一个设计 | 设定图工作流 + 多参考模型 |
| ④ 序列帧一致 | 动画帧间漂移 | 视频模型抽帧 + 帧对齐（最难，纯抽帧撑不到发售） |

**关键认知**：越往上越不能靠「写好提示词」，只能靠工程化（参考图管线 / LoRA）。选工具时真正要比的是**「产出离可用最近、返工成本最低」**，不是「哪张演示图最惊艳」。

---

## 三、2026-11 工具格局（闭源主力）

### 通用大模型

| 模型 | 单张成本（约） | 商用 | 定位 |
|---|---|---|---|
| **Nano Banana 2.1 / Pro**（Google） | 2.1 ≈ $0.04；Pro $0.134（4K $0.24） | 可商用，**但免费档/AI Pro 档有可见 ✨ 水印**，只有 AI Ultra 或付费 API 无水印 | 提示词遵循、多图融合、对话改图综合第一梯队；最多 5 角色 / 14 物体一致性 |
| **GPT Image 2 / 2.5**（OpenAI） | low $0.005 / medium $0.05 / high $0.21 | 可商用 | 文字渲染 99%+、2K 原生。**low 档抽卡 + medium 定稿**是最省钱打法 |
| **Midjourney V8.2** | 订阅 $10 / $30 / $60 / $120 每月 | 付费档可商用 | 风格化/审美天花板。V8.2 Edit Model 支持文字指令改图 + 4 参考图。**Stealth Mode（不公开）仅 Pro/Mega** |
| **Seedream 5.0 Pro**（字节） | Pro $0.075；4.0 $0.03；火山方舟 ¥0.2 | 可商用（走方舟 API） | **最多 14 张参考图融合**，多参考最强 |
| **Grok Imagine 2.0**（xAI） | $0.04~$0.08 | 可商用 | 快、便宜，精细控制弱于上面 |

> ⏰ **时效**：Midjourney 官方在 2026-11-18 Office Hours 说 **V9 目标 12 月初发布**，现在还没出，最新是 V8.2。别急着冲 V9。

### 二次元专项（重点）

| 模型 | 状态 | 说明 |
|---|---|---|
| **Niji 8**（Midjourney，`--niji 8`） | **2026-11-24 刚上线** | 动漫特化，自带独立 edit model 取代 Niji 6 的 cref，做「同角色换姿势/背景」；官方说 V8 偏向多样性，一致性靠 edit 那一步补 |

你们如果是二次元项目，这条是本周最该试的。

### 矢量 / 图标（这块别用通用模型）

| 服务 | 能力 | 价格 | 条款红线 |
|---|---|---|---|
| **Recraft V4** | 真 SVG 矢量、图标集（一次整套风格统一）、Brand Styles | Raster $0.04 / Vector $0.08 / Pro Vector $0.30；订阅 $10/月起 | **付费/API 完全拥有输出可商用，退订仍保留**；免费档输出公开且归 Recraft，**禁止商用** |
| **Ideogram 4** | 可编辑文字层 + alpha 通道 | $0.03~0.26 | 权重已开源（9.3B） |
| **Adobe Firefly**（Image Model 5） | 训练数据授权合规 + **企业 IP 赔偿 indemnification** | Standard $9.99 ≈ 200 张/月 | 法务最稳，风格化上限低于 MJ |

### 游戏垂直平台

| 平台 | 独特能力 | 价格 | 适合 |
|---|---|---|---|
| **Leonardo.Ai** | **透明 PNG 直出**（省抠图）、UV 贴图生成、Elements 风格叠加器 | Free 150 token/天；Essential $12 | 独立游戏 2D 一站式 |
| **Scenario** | **自训专属风格模型**（15 张自家美术即可）、等距 tileset 工作流 | Free 50 积分/天；Starter $15 / Pro $45 | 需要全队统一画风 |
| **Layer.ai** | 聚合 149+ 模型的「工作室 OS」、PBR 无缝贴图 + PSD 导出、不收席位费 | 订阅制 | 团队协作 + 贴图管线 |

**Leonardo vs Scenario 怎么选**：一个人要快速出成品 → Leonardo（透明直出省两道工序）；有明确自家画风要训 → Scenario。

### 像素专项（如果是像素游戏）

| 工具 | 价格 | 备注 |
|---|---|---|
| **PixelLab** | $12/月起（约 1000 张）；API 32×32 ≈ $0.029 | 8 方向角色旋转、精灵动画、tileset、参考图锁风格，有 Aseprite 插件 |
| **Retro Diffusion** | **$65 一次性买断**（Lite $20） | Aseprite 扩展，本地推理、可商用，16 色系统级输出 |

选法：要「生成→在 Aseprite 里接着画」一体流 → Retro Diffusion 买断；要 8 方向 + 动画 + API 量产 → PixelLab。

### 国内可达（中文 / 支付方便）

| 服务 | 价格 | 商用 |
|---|---|---|
| 即梦 Dreamina | 免费额度/日；基础 ¥79/月（连续包月 ¥41） | 可商用，输出权益归用户 |
| 火山方舟（Seedream 系） | ¥0.2/张 | **豆包 App 条款模糊，商用走方舟 API** |
| 通义万相 API | ¥0.2/张，失败不计费 | 可商用，企业协议清晰 |
| 腾讯混元生图 API | ¥0.24~0.26/张 | 可商用，企业协议清晰 |
| LiblibAI | 免费 300 算力/日；年费 ¥429 起 | **必须选「商用无忧」标签的模型** |

---

## 四、落地流程：定稿 → 量产两步法（照这个做，别跳）

### 第一步：出「标准像」

用最强模型 + 最细 prompt，出一张**角色设定图**：三视图 + 表情表 + 固定背景。

```
{全局风格段}, {角色设定段},
character design sheet, three views (front view, side view, back view),
expression chart with 4 faces, consistent proportions, flat white background
```

一次出 8~16 张候选，**挑 1 张定为「标准像」**，之后一切生产以它为锚。

### 第二步：以标准像为锚量产

| 生产什么 | 用什么 | 要点 |
|---|---|---|
| 换姿态/表情差分 | 指令编辑（Qwen-Edit / Nano Banana） | 底图信息全保留，一致性天然最好，**这是 2026 年差分主力** |
| 新构图/新场景 | 垫图（IP-Adapter / PuLID）+ prompt | 权重 0.6~0.8 起调：高了僵、低了漂 |
| 复杂新视角 | 多参考融合（Seedream 14 图 / Qwen-Edit 多图） | 参考图必须同风格同角色，否则生成「缝合怪」 |
| 量产 ≥50 张 / 团队复用 | 训角色 LoRA | 触发词替代主体描述 |

### 封版纪律（最容易被忽视的一条）

定稿那一刻起，**底模、采样参数、STYLE 前缀、标准像**四样全部锁进项目文档，量产期间不换。任何「顺手升级一下模型」的冲动都留到下一批资产。

### LoRA 什么时候该训

① 垫图跑了几百张仍频繁漂移；② 同一画风/角色要用在 50 张以上；③ 多人协作需要「画风资产化」。

- 数据集：画风 30~100 张；角色 20~50 张（**20 张合格图就能开训第一版**）
- 清洗比数量重要：统一比例 1024、背景干净、剔除水印和多余额外道具
- 参数：rank 8~32（角色用 8~16 就够）、lr 1e-4、epochs 10~15
- 工具：本地 `kohya sd-scripts`（最大控制力）/ `OneTrainer`（GUI 最全，新手友好）/ 云端 Civitai 站内训练器（没显卡时用）

### QC 检查单（打印贴墙上，每 10 张抽检一次）

- [ ] 头身比符合规范
- [ ] 角色「记忆点」齐全且位置正确（耳朵/尾巴/背部花纹）
- [ ] 四肢数量正确、无畸形
- [ ] 与标准像比对：配色、花纹位置不漂移
- [ ] 交付件透明底边缘干净、无白边

**漂移是常态不是失败。** 正确姿势是把检查前移到每 10 张抽一次，发现立即回标准像重垫图，而不是 200 张出完再返工。

---

## 五、五个一定会踩的坑

1. **免费档当商用档用。** Gemini 免费档/AI Pro 档有可见 ✨ 水印；Recraft 免费档禁商用且版权归 Recraft；Rosebud 免费档仅非商用。「免费」和「可商用」是两件事。
2. **订阅和 API 选错。** 月出图 <200 张用订阅（MJ/即梦/Leonardo），>500 张用 API 按张。订阅积分用不完是常态浪费。
3. **只看单张价，不算重试率。** 重试率和低档质量带来的返工时间都是成本。GPT low 抽卡 + medium 定稿通常比全程 medium 省一半。
4. **忽略条款责任归属。** Midjourney 把侵权责任转给用户；企业级项目要 indemnification 就看 Firefly / Vertex AI。
5. **把对话式工具当量产工具。** Nano Banana Pro 改图很爽，但它面向人肉操作，批量差分走它成本是脚本路线的 2~3 倍。

### 画风纪律

- 一上来就训 LoRA = 把混乱固化。顺序必须是：**STYLE 前缀 → 标准像 → 垫图 → 实在不行再 LoRA**
- LoRA 权重拉满（1.0）常见塑料感和过拟合，0.7~0.9 是常用区间
- 画风稳定后给 LoRA/prompt/参数打版本号，否则三个月后没人说得清「这批图是怎么出来的」

---

## 六、给你们的推荐起步路径

**假设：小团队、预算有限、要能上商用项目。**

### 阶段 1：一周内验证可行性（¥0 ~ ¥100）

1. **Recraft V4 免费档**跑一套 8 个 UI 图标，看能不能直接用（注意：免费档禁商用，只用来判断可行性）
2. **Niji 8 / Midjourney Basic $10** 出一张角色设定图，感受风格化上限
3. **即梦 / 豆包**试中文提示词友好度

### 阶段 2：定画风 + 主要工具（¥200~500/月）

- 图标 → **Recraft 订阅 $10/月起**（拿到商用授权）
- 角色 → **Midjourney Standard $30**（含 Stealth Mode 需要 Pro $60）+ 如果偏二次元重点压 Niji 8
- 改图/差分 → **Nano Banana Pro API** 或 **GPT Image 2**（low 档抽卡）

### 阶段 3：量产要一致性（一次性投入 + API）

- 攒够 20~50 张合格图 → 训**角色 LoRA**（本地有卡就 ComfyUI，没卡用 Scenario / LiblibAI 商用无忧模型）
- 大批量 → 走 **API 按张**（GPT Image 2 low $0.005 或 Seedream 4.0 $0.03）

### 硬件参考（你们的机器）

Y9000P 那台 RTX 5060 Laptop 8GB 显存，能跑：
- ✅ SDXL 8~12GB（量化/优化后）、Illustrious/NoobAI-XL 6~8GB —— 动漫 + LoRA 生态最厚
- ✅ Z-Image Turbo 16GB 需量化、FLUX.2 klein 4B 8~12GB
- ❌ Qwen-Image 24GB、FLUX.2 dev 32GB+ —— 这两类走云端

所以本地跑**动漫画风 + LoRA 训练**是可行的，Qwen-Edit 这种一致性之王走 API 或云端。

---

## 七、参考文献

- [AI 游戏美术手册](https://sena.games/ai-art/guide/13-resources)（基线 2026-09，第 3/4/10/13 章）
- [Midjourney 文档](https://docs.midjourney.com)
- [Niji 8 上线报道](https://www.fathom.news/midjourney-niji-v8/)（2026-11-24）
- [Midjourney V9 时间表](https://geniart.fr/midjourney/office-hours/midjourney-v9-debut-decembre-niji/)（目标 12 月初）
- [Nano Banana Pro 官方页](https://deepmind.google/models/gemini-image/pro/)
- [Gemini 图像 API 与水印文档](https://ai.google.dev/gemini-api/docs/image-generation)
- [Recraft 商用授权 FAQ](https://www.recraft.ai/blog/ownership-and-commercial-use-faq)
- [OpenAI 定价](https://developers.openai.com/api/docs/pricing)
- [Scenario](https://www.scenario.com) · [Leonardo 定价](https://leonardo.ai/pricing) · [Layer](https://layer.ai)
- [PixelLab](https://www.pixellab.ai) · [Retro Diffusion](https://astropulse.itch.io/retrodiffusion)
