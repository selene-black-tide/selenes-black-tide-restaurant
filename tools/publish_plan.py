# -*- coding: utf-8 -*-
"""
一键发布企划书：导出 md -> 提交 -> 推送。

用法（仓库根目录）：
    python tools/publish_plan.py

你只需要在 Word 里改 游戏企划书.docx，然后跑这一条命令。
它会自动把 docx 重新导出成 md，一起提交并推给别人看。

为什么需要这一步
----------------
GitHub 不渲染 .docx，别人点开只能下载。
所以「给别人看」的其实是同目录的 游戏企划书.md——它是机器/浏览器都能直接读的版本。
忘了跑的后果：别人看到的还是上一版。
"""
from __future__ import annotations

import datetime
import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCX = "docs/00-overview/游戏企划书.docx"
MD = "docs/00-overview/游戏企划书.md"


def find_git() -> str:
    """找 git 的绝对路径。

    为什么不直接写 "git"：双击运行时继承的是 Explorer 的环境变量，
    有时候还没刷新到最新 PATH（Git 装完要重开终端才生效），
    那时候 subprocess 找不到 git，会直接抛 FileNotFoundError。
    """
    p = shutil.which("git")
    if p:
        return p
    candidates = [
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\cmd\git.exe"),
    ]
    candidates += glob.glob(
        os.path.expandvars(r"%LOCALAPPDATA%\GitHubDesktop\app-*\resources\app\git\cmd\git.exe")
    )
    for c in candidates:
        if os.path.exists(c):
            return c
    return ""


GIT = find_git()

# Windows 控制台默认 GBK，子进程默认也按 GBK 输出，两边一混就乱码/报错。
# 统一让子进程用 UTF-8，自己这边打印时做一次兜底。
_CHILD_ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")


def say(text: str = "") -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("gbk", "replace").decode("gbk", "replace"))


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(
        cmd, cwd=ROOT, capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=_CHILD_ENV,
    )
    if check and r.returncode != 0:
        say(r.stdout.strip())
        say(r.stderr.strip())
        sys.exit(f"命令失败：{' '.join(cmd)}")
    return r


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return run([GIT, *args], check=check)


def main() -> None:
    if not (ROOT / ".git").exists():
        sys.exit(f"这里不是 git 仓库：{ROOT}")

    if not GIT:
        sys.exit(
            "找不到 git。\n"
            "装一个：winget install --id Git.Git -e --source winget\n"
            "装完重开一个终端窗口再试。"
        )

    # 1. 导出 md
    say("[1/4] 导出 游戏企划书.md ...")
    r = run([sys.executable, "tools/export_plan.py"])
    for line in r.stdout.strip().splitlines():
        say("    " + line)

    # 2. 暂存 docx + md
    say("[2/4] 暂存 docx 与 md ...")
    git("add", DOCX, MD)

    # 3. 有没有变化
    staged = git("diff", "--cached", "--name-only", check=False)
    if not staged.stdout.strip():
        say("[3/4] 没有任何改动，跳过提交。")
        say("       （docx 没变，或者改了但内容一模一样）")
        return
    say("[3/4] 要提交的文件：")
    for f in staged.stdout.strip().splitlines():
        say(f"      {f}")

    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    git("commit", "-m", f"docs(overview): 更新企划书 {stamp}")

    # 4. 推送
    say("[4/4] 推送 ...")
    r = git("push", check=False)
    if r.returncode != 0:
        say(r.stdout.strip())
        say(r.stderr.strip())
        say()
        say("推送被拒绝，通常是远端有别人的新提交。手动处理：")
        say("    git pull --rebase")
        say("    git push")
        sys.exit(1)

    say()
    say("完成。别人刷新网页就能看到最新版：")
    say("    https://github.com/selene-black-tide/selenes-black-tide-restaurant"
        "/blob/main/docs/00-overview/游戏企划书.md")


if __name__ == "__main__":
    main()
