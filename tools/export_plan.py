# -*- coding: utf-8 -*-
"""
把 docs/00-overview/游戏企划书.docx 导出成同名 Markdown 镜像。

为什么存在
----------
docx 是二进制，四家 AI（GPT / Claude / Gemini / DeepSeek）直接读会乱码。
这份 .md 是给机器读的镜像，**源永远是 docx**。

规矩
----
1. 改内容 -> 改 docx -> 重跑本脚本。**不要手改生成的 .md**，下次导出会被覆盖。
2. 本脚本只做「结构还原」，不改写任何一个字。
3. 原 docx 里 124 个段落全是 Normal 样式、没有标题层级，所以标题是**按关键词认出来的**。
   新增章节如果认不出来，会原样降级成普通段落，不会丢内容。

用法
----
    python tools/export_plan.py
"""
from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

try:
    import docx  # python-docx
except ImportError:
    sys.exit("缺 python-docx，先跑：pip install python-docx")

ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "docs" / "00-overview" / "游戏企划书.docx"
MD = ROOT / "docs" / "00-overview" / "游戏企划书.md"

# 一级章节：docx 里这些词开头的段落提成 ##
TOP_WORDS = [
    "游戏主体玩法", "艺术风格", "模拟经营部分", "可升级的项目", "关于掉落物",
    "肉鸽部分", "基础怪物设计", "主线剧情设计", "制作任务&方向", "资源&资金",
    "地图设计",
]

# 二级章节：怪物条目之类
SUB_RE = re.compile(r"^(敌怪\s*\d+|精英\s*\d+.*|boss|以下为.+|三小只|四小只|【地图.*)\s*$", re.I)

# 「标签：内容」的短标签
LABEL_RE = re.compile(r"^([^：:]{1,10})[：:]\s*(.*)$")


def classify(text: str):
    """返回 (kind, 主标题, 剩余正文)。kind: h2 / h3 / quote / label / p"""
    for w in TOP_WORDS:
        if text.startswith(w):
            rest = text[len(w):].lstrip("：: ").strip()
            return "h2", w, rest

    if SUB_RE.match(text):
        return "h3", text, ""

    if text.startswith("【"):
        # 长的【聊天原文：…】是引文块；短的【地图1 这类是小标题
        return ("quote" if len(text) > 40 else "h3"), text, ""

    m = LABEL_RE.match(text)
    if m and len(text) <= 60:
        return "label", m.group(1), m.group(2)

    return "p", text, ""


def convert() -> str:
    d = docx.Document(str(DOCX))

    lines: list[str] = []
    for para in d.paragraphs:
        t = para.text.strip()
        if not t:
            lines.append("")
            continue

        kind, head, rest = classify(t)
        if kind == "h2":
            lines.append(f"## {head}")
            if rest:
                lines.append(rest)
        elif kind == "h3":
            lines.append(f"### {head}")
        elif kind == "quote":
            lines.append(f"> {head}")
        elif kind == "label":
            lines.append(f"**{head}**：{rest}" if rest else f"**{head}**：")
        else:
            lines.append(head)

    body = "\n".join(lines)
    body = re.sub(r"\n{3,}", "\n\n", body)                 # 收掉连续空行
    body = re.sub(r"([^\n])\n(#{1,3} )", r"\1\n\n\2", body)  # 标题前空行
    body = re.sub(r"(#{1,3} [^\n]+)\n([^\n#])", r"\1\n\n\2", body)  # 标题后空行
    body = body.strip()
    return body, len(d.paragraphs)


HEADER = """<!-- 本文件由 tools/export_plan.py 自动生成，请勿手改 -->

> **⚠️ 这是自动生成的镜像，不是源文件。**
> 源文件：[游戏企划书.docx](游戏企划书.docx) —— 改内容请改 **docx**，然后跑 `python tools/export_plan.py` 重新导出。
> 导出自：{stamp} · 源段落数 {n}

# 游戏企划书 · Selene's Black Tide Restaurant

> 项目正式定稿，**一切设计的最高依据**。这是给机器读的 Markdown 版本，结论以同目录的 docx 为准。

---
"""

SEP = "\n---\n\n"


def main() -> None:
    if not DOCX.exists():
        sys.exit(f"找不到源文件：{DOCX}")

    body, n = convert()

    # 内容没变就不重写，避免每次导出都刷时间戳、产生无意义 diff
    if MD.exists():
        old = MD.read_text(encoding="utf-8").replace("\r\n", "\n")
        old_body = old.split(SEP, 1)[1] if SEP in old else ""
        if old_body.strip() == body.strip():
            print(f"OK  内容无变化，保持原文件：{MD.relative_to(ROOT)}")
            return

    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    text = HEADER.format(stamp=stamp, n=n) + "\n" + body + "\n"

    # newline="\n" 强制 LF，跟 .gitattributes 的 eol=lf 对齐
    with open(MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

    print(f"OK  已导出 {MD.relative_to(ROOT)}")
    print(f"    {len(text)} 字符 / {text.count(chr(10))} 行")


if __name__ == "__main__":
    main()
