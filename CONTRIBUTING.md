# CONTRIBUTING.md —— 协作规范

> 给人和 AI 看的同一份东西。AI 的硬规则在 [AGENTS.md](AGENTS.md)，这里是**流程**。

## 一句话

**改文档 → 登记 INDEX → 提交一次 → 推 main。** 大改走 PR。

---

## 1. 日常流程

```powershell
git pull                      # 先拉，别在旧版本上改
# ...改东西...
git add -A
git commit -m "docs(art): 补 NAI 差分工作流"
git push
```

**分支策略**（小团队，别搞重的）：

| 情况 | 怎么做 |
|---|---|
| 改文档、补内容、改错字 | 直接推 `main` |
| 动设计结论、动 SOT | 开分支 + PR，至少一个人看过再合 |
| 代码 | 一律 PR，别直接推 main |

## 2. 新增一份文档（四步，别漏第三步）

1. 放到对应目录：`docs/10-design/系统-XXX.md`
2. 复制 [docs/10-design/_模板.md](docs/10-design/_模板.md) 的头部，填 frontmatter
3. **在 [INDEX.md](INDEX.md) 加一行** ← 最容易漏，漏了等于没写
4. 提交：`docs(设计): 新增 XXX`

## 3. 提交信息

```
类型(范围): 一句话说明
```

- 类型：`feat` `fix` `docs` `design` `art` `chore`
- 范围：`demo`（经营）/ `run`（肉鸽）/ `art`（美术）/ `repo`（仓库本身）
- 说清**做了什么**，不要写「更新」「修改」「fix」

| ❌ | ✅ |
|---|---|
| `update` | `docs(art): 补像素资产的 QC 清单` |
| `修改文档` | `design(经营): 风评改为按当天满足率计算` |
| `fix bug` | `fix(run): 体力条归零后没能回店` |

## 4. 中文文件名：已知的取舍

- **文件名用中文**，团队读起来快，四家 AI 也都认得
- **目录名用英文**，URL 干净
- 已在 `.git config` 里设 `core.quotepath=false`，否则 `git status` 会把中文名显示成 `\346\270\270`
- **首次 clone 后必须设一次**，否则你看到的全是乱码：

```powershell
git config --global core.quotepath false
```

## 5. 大文件

- `.psd` / `.aseprite` / 音频 / 字体：已在 `.gitattributes` 里配 Git LFS，直接 `git add` 即可
- **队友必须装 git-lfs**（GitHub Desktop 自带，命令行装 `winget install Git.Git` 就带）
- 超过 5 MB 的 `.png`：先问一句再提交
- 不要把 `assets/` 整个塞进去，按模块分：`assets/demo/`、`assets/run/`

## 6. 不做的事

- ❌ 不删别人的文档——要废就改 `status: 废案` 并挪进 `docs/90-archive/`
- ❌ 不提交 `_tmp/`、`~$*.docx`、`*.bak-*`（已进 `.gitignore`）
- ❌ 不为了「看起来完整」而建空文件、写 `TODO`
- ❌ 不在仓库里放密钥、`.env`、个人路径

## 7. 用 AI 干活的姿势

把 [AGENTS.md](AGENTS.md) **整个文件**贴给 AI，再贴你要它干的活。不要只丢一句「帮我写个系统设计」——它不知道术语、不知道哪些定了哪些没定，写出来 80% 要返工。

**各家 AI 的入口文件**（内容都指向 AGENTS.md，不用重复维护）：

| AI | 自动读的文件 |
|---|---|
| GPT / Codex / 通用 Agent | `AGENTS.md` |
| Claude Code | `CLAUDE.md` |
| Gemini CLI | `GEMINI.md` |
| GitHub Copilot | `.github/copilot-instructions.md` |
| 网页版（ChatGPT / Claude / Gemini 对话） | 不会自动读，**手动贴 AGENTS.md** |
