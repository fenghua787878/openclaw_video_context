#!/usr/bin/env python3
"""
内容抓取执行器（过渡层）。
输入：一组 URL（文件路径或 argv）
输出：items.jsonl（每行一个 JSON），含 reliability/notes。
使用 requests + 可选的 readability/bs4；未安装则回退纯文本提取。
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# 可选依赖（注释提示）：pip install requests beautifulsoup4 readability-lxml
try:
    import requests
except ImportError:
    requests = None  # type: ignore

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None  # type: ignore

try:
    from readability import Document
except ImportError:
    Document = None  # type: ignore


def _headers() -> dict[str, str]:
    return {
        "User-Agent": "ContentLoop/1.0 (compatible; fetch_content)",
    }


def fetch_url(url: str, timeout: int = 15) -> tuple[str, str, str]:
    """
    拉取 URL 正文。返回 (title, content, error)。
    error 为空表示成功。
    """
    if not requests:
        return "", "", "requests not installed"
    try:
        r = requests.get(url, headers=_headers(), timeout=timeout)
        r.raise_for_status()
        html = r.text
    except Exception as e:
        return "", "", str(e)

    title = ""
    content = ""

    if Document and BeautifulSoup:
        try:
            doc = Document(html)
            title = doc.title() or ""
            content = doc.summary() or ""
            if content:
                soup = BeautifulSoup(content, "html.parser")
                content = soup.get_text(separator="\n", strip=True)
        except Exception:
            pass

    if not content and BeautifulSoup:
        try:
            soup = BeautifulSoup(html, "html.parser")
            for tag in ("script", "style", "nav", "footer", "header"):
                for t in soup.find_all(tag):
                    t.decompose()
            title = (soup.find("title") or soup.find("h1"))
            if title:
                title = title.get_text(strip=True)
            body = soup.find("body") or soup
            content = body.get_text(separator="\n", strip=True)
            content = re.sub(r"\n{3,}", "\n\n", content)
        except Exception:
            pass

    if not content:
        content = html[:5000] if len(html) > 5000 else html
        content = re.sub(r"<[^>]+>", " ", content)
        content = re.sub(r"\s+", " ", content).strip()

    return title or urlparse(url).path or url, content or "(empty)", ""


def urls_from_args() -> list[tuple[str, str]]:
    """返回 [(signal_id, url), ...]。支持 argv 或文件（每行 signal_id,url 或仅 url）。"""
    urls: list[tuple[str, str]] = []
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            p = Path(arg)
            if p.is_file():
                for line in p.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split(",", 1)
                    if len(parts) == 2:
                        urls.append((parts[0].strip(), parts[1].strip()))
                    else:
                        urls.append((f"sig_{len(urls)+1:03d}", line))
            else:
                urls.append((f"sig_{len(urls)+1:03d}", arg))
    return urls


def main() -> int:
    pairs = urls_from_args()
    if not pairs:
        print(
            "usage: fetch_content.py <url> [url ...]\n"
            "   or: fetch_content.py <file>  # file: one url per line or 'signal_id,url'",
            file=sys.stderr,
        )
        return 1

    out_path = os.environ.get("OUT_ITEMS")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    lines: list[str] = []

    for signal_id, url in pairs:
        title, content, err = fetch_url(url)
        if err:
            item: dict[str, Any] = {
                "signal_id": signal_id,
                "url": url,
                "title": title or url,
                "content": content[:2000] if content else "(fetch failed)",
                "reliability": "low",
                "notes": "fetch_failed",
                "fetched_at": now,
            }
        else:
            item = {
                "signal_id": signal_id,
                "url": url,
                "title": title,
                "content": content[:15000],
                "reliability": "high",
                "notes": "",
                "fetched_at": now,
            }
        lines.append(json.dumps(item, ensure_ascii=False))

    payload = "\n".join(lines)
    if out_path:
        p = Path(out_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(p)
        print(f"Wrote {len(lines)} items to {out_path}", file=sys.stderr)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
