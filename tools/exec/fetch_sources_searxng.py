#!/usr/bin/env python3
"""
信号发现执行器（使用 SearXNG）。
输入：关键词（argv 或 env QUERY/KEYWORDS）
输出：signals.json 或 stdout JSON。
使用本地 SearXNG 实例进行搜索。
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Any, List, Dict

# 可选：从项目根加载 src
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from src.run_id import make_signal_id
except ImportError:
    def make_signal_id(i: int) -> str:
        return f"sig_{i:03d}"


def get_keywords() -> list[str]:
    """从 argv 或环境变量获取关键词。"""
    if len(sys.argv) > 1:
        return sys.argv[1:]
    raw = os.environ.get("QUERY") or os.environ.get("KEYWORDS") or ""
    if not raw:
        return []
    return [s.strip() for s in raw.split(",") if s.strip()]


def search_searxng(query: str, num_results: int = 10) -> List[Dict[str, Any]]:
    """使用 SearXNG 搜索查询。"""
    try:
        # SearXNG API endpoint
        searxng_url = "http://localhost:8080/search"
        
        # 构建查询参数
        params = {
            'q': query,
            'format': 'json',
            'pageno': 1,
            'language': 'zh-CN'
        }
        
        url = searxng_url + '?' + urllib.parse.urlencode(params)
        
        # 发送请求
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'ContentLoop/1.0')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        signals = []
        for i, result in enumerate(data.get('results', [])[:num_results]):
            signals.append({
                "id": make_signal_id(i + 1),
                "title": result.get('title', 'No title'),
                "url": result.get('url', ''),
                "source": result.get('host', 'unknown'),
                "published_at": "unknown",  # SearXNG 不提供发布日期
                "reason": f"Relevant to query: {query}",
                "score": max(5.0, 10.0 - i * 0.5)  # 基于排名的评分
            })
            
        return signals
        
    except Exception as e:
        print(f"Error searching SearXNG: {e}", file=sys.stderr)
        return []


def main() -> int:
    keywords = get_keywords()
    if not keywords:
        print(
            "usage: fetch_sources_searxng.py <keyword1> [keyword2 ...]\n"
            "   or: QUERY='kw1,kw2' fetch_sources_searxng.py",
            file=sys.stderr,
        )
        return 1

    all_signals = []
    signal_counter = 1
    
    # 对每个关键词进行搜索
    for keyword in keywords[:5]:  # 限制最多5个关键词
        signals = search_searxng(keyword, num_results=3)  # 每个关键词3个结果
        for signal in signals:
            signal["id"] = make_signal_id(signal_counter)
            all_signals.append(signal)
            signal_counter += 1
            
        if len(all_signals) >= 10:  # 目标10条信号
            break
    
    # 如果没有找到任何信号，返回一些示例
    if not all_signals:
        all_signals = [
            {
                "id": "sig_001",
                "title": "【SearXNG Search Failed】海南自贸港数字资产合规指南",
                "url": "https://example.com/searxng-failed",
                "source": "fallback",
                "published_at": "unknown",
                "reason": "SearXNG search failed, using fallback content",
                "score": 4.0
            },
            {
                "id": "sig_002",
                "title": "【SearXNG Search Failed】中国加密货币监管政策解读",
                "url": "https://example.com/searxng-failed-2",
                "source": "fallback",
                "published_at": "unknown",
                "reason": "SearXNG search failed, using fallback content",
                "score": 4.0
            }
        ]

    out = os.environ.get("OUT_SIGNALS")
    payload = json.dumps(all_signals, ensure_ascii=False, indent=2)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(payload, encoding="utf-8")
        print(f"Wrote {len(all_signals)} signals to {out}", file=sys.stderr)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())