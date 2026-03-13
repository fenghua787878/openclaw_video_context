#!/usr/bin/env python3
"""将 runs/<run_id>/script.md 拆分为脚本条目，并生成 Notion 写入命令。"""
from __future__ import annotations

import argparse
import re
import shlex
import subprocess
from pathlib import Path


def parse_script_blocks(script_text: str) -> list[tuple[str, str]]:
    """解析 script.md 中的“## 脚本 N”分块，返回 (script_id, body) 列表。"""
    pattern = re.compile(r"^##\s*脚本\s*(\d+)\s*$", re.MULTILINE)
    matches = list(pattern.finditer(script_text))
    if not matches:
        return []

    blocks: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(script_text)
        sid = f"script_{m.group(1)}"
        body = script_text[start:end].strip()
        blocks.append((sid, body))
    return blocks


def build_notion_command(
    run_id: str,
    script_id: str,
    text: str,
    content_category: str,
    expression_variant: str,
) -> str:
    text_one_line = " ".join(text.split())
    if len(text_one_line) > 1800:
        text_one_line = text_one_line[:1800] + " …(truncated for command)"
    return (
        "调用 notion create_page 文本升级观测 "
        f"{{文本ID:{run_id}_{script_id},"
        f"文本正文:{text_one_line},"
        "播放量:0,点赞量:0,粉丝量:0,"
        f"内容方向:{content_category},"
        f"表达方式:{expression_variant}}}"
    )


def maybe_exec_command(command_line: str) -> tuple[int, str]:
    """尝试调用本地 notion CLI；失败时返回错误信息。"""
    if not command_line.startswith("调用 notion "):
        return 1, "command must start with '调用 notion '"
    cli = "notion " + command_line[len("调用 notion ") :]
    try:
        out = subprocess.run(
            shlex.split(cli),
            check=False,
            capture_output=True,
            text=True,
        )
        msg = (out.stdout or "") + (out.stderr or "")
        return out.returncode, msg.strip()
    except FileNotFoundError:
        return 127, "notion CLI not found in PATH"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--script-path", default="")
    ap.add_argument("--content-category", default="政策解读")
    ap.add_argument("--expression-variant", default="问答式")
    ap.add_argument("--write-commands", default="")
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()

    script_path = Path(args.script_path) if args.script_path else Path("runs") / args.run_id / "script.md"
    if not script_path.exists():
        raise SystemExit(f"script not found: {script_path}")

    text = script_path.read_text(encoding="utf-8")
    blocks = parse_script_blocks(text)
    if not blocks:
        raise SystemExit("no script blocks found (expecting '## 脚本 N')")

    commands = [
        build_notion_command(
            run_id=args.run_id,
            script_id=sid,
            text=body,
            content_category=args.content_category,
            expression_variant=args.expression_variant,
        )
        for sid, body in blocks
    ]

    out_path = (
        Path(args.write_commands)
        if args.write_commands
        else Path("runs") / args.run_id / "notion_sync_commands.txt"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(commands) + "\n", encoding="utf-8")
    print(f"wrote {len(commands)} command(s) to {out_path}")

    if args.execute:
        for cmd in commands:
            code, msg = maybe_exec_command(cmd)
            print(f"[exec] rc={code} cmd={cmd}")
            if msg:
                print(msg)
            if code != 0:
                return code

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
