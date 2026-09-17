#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COSMO 市场分析报告生成器
从 keyword-cosmo-attribute-*-v41.csv 产出 HTML + Excel（可筛选词明细 + 各维副表汇总）。
多标签（a|b）搜索量等分，口径在说明中标注。
"""

from __future__ import annotations

import argparse
import csv
import html
import math
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.table import Table, TableStyleInfo
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "需要 openpyxl。请使用 /workspace/venv-ads/bin/python 或 pip install openpyxl"
    ) from e


# ---------------------------------------------------------------------------
# Column aliases (Chinese headers preferred)
# ---------------------------------------------------------------------------

ATTR_DIMS = [
    "目标人群",
    "修饰/价值",
    "购买场所",
    "季节/节日",
    "场景/活动",
    "产地/文化",
    "通用/品类",
    "成分/材质",
    "痛点/需求",
    "产品形态",
    "使用部位",
    "功效",
    "风格属性",
]

CORE_COLS = [
    "序号",
    "关键词",
    "搜索量",
    "流量等级",
    "竞品数",
    "蓝海度",
    "ABA转化份额",
    "准入难度",
    "竞品表现得分",
    "相关性等级",
    "推荐行动",
]

COL_ALIASES = {
    "序号": ["序号", "index", "id", "#"],
    "关键词": ["关键词", "keyword", "search term", "phrase"],
    "搜索量": ["搜索量", "search volume", "volume", "sv", "月搜索量"],
    "流量等级": ["流量等级", "traffic tier", "tier"],
    "竞品数": ["竞品数", "competitors", "competing products"],
    "蓝海度": ["蓝海度", "blue ocean", "competition"],
    "ABA转化份额": ["ABA转化份额", "aba", "aba share"],
    "准入难度": ["准入难度", "entry difficulty"],
    "竞品表现得分": ["竞品表现得分", "competitor score"],
    "相关性等级": ["相关性等级", "relevance"],
    "推荐行动": ["推荐行动", "action", "recommendation"],
}
for d in ATTR_DIMS:
    COL_ALIASES[d] = [d]


def _norm_header(h: str) -> str:
    return re.sub(r"\s+", "", (h or "").strip().lower())


def map_columns(fieldnames: Sequence[str]) -> Dict[str, str]:
    """Map canonical name -> actual CSV header."""
    actual = { _norm_header(f): f for f in fieldnames if f }
    mapping: Dict[str, str] = {}
    for canon, aliases in COL_ALIASES.items():
        for a in aliases:
            key = _norm_header(a)
            if key in actual:
                mapping[canon] = actual[key]
                break
        # also try exact match on original
        if canon not in mapping:
            for f in fieldnames:
                if f == canon:
                    mapping[canon] = f
                    break
    return mapping


def parse_float(v: Any) -> float:
    if v is None:
        return 0.0
    s = str(v).strip().replace(",", "")
    if s in ("", "-", "—", "N/A", "n/a", "无数据", "null"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        m = re.search(r"[-+]?\d*\.?\d+", s)
        return float(m.group()) if m else 0.0


def parse_tags(raw: Any) -> List[str]:
    if raw is None:
        return []
    s = str(raw).strip()
    if s in ("", "-", "—", "N/A", "n/a", "无"):
        return []
    parts = re.split(r"[|｜;/；、]+", s)
    out = []
    seen = set()
    for p in parts:
        t = p.strip()
        if not t or t in ("-", "—"):
            continue
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def percentile(sorted_vals: List[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)


# ---------------------------------------------------------------------------
# Load & analyze
# ---------------------------------------------------------------------------

def load_rows(path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, str], List[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit(f"CSV 无表头: {path}")
        colmap = map_columns(reader.fieldnames)
        if "关键词" not in colmap:
            raise SystemExit(f"缺少关键词列。实际表头: {reader.fieldnames}")
        raw_rows = list(reader)

    rows: List[Dict[str, Any]] = []
    for i, r in enumerate(raw_rows, 1):
        kw = (r.get(colmap["关键词"]) or "").strip()
        if not kw:
            continue
        vol = parse_float(r.get(colmap.get("搜索量", ""), 0))
        item: Dict[str, Any] = {
            "_i": i,
            "序号": (r.get(colmap.get("序号", ""), "") or str(i)),
            "关键词": kw,
            "搜索量": vol,
        }
        for c in CORE_COLS:
            if c in ("序号", "关键词", "搜索量"):
                continue
            if c in colmap:
                item[c] = (r.get(colmap[c]) or "").strip()
            else:
                item[c] = ""
        for d in ATTR_DIMS:
            raw = r.get(colmap[d], "") if d in colmap else ""
            tags = parse_tags(raw)
            item[d] = tags
            item[f"{d}__raw"] = (raw or "").strip() if isinstance(raw, str) else str(raw or "")
        rows.append(item)
    return rows, colmap, list(reader.fieldnames or [])


def fill_rate(rows: List[Dict[str, Any]], dim: str) -> float:
    if not rows:
        return 0.0
    n = sum(1 for r in rows if r.get(dim))
    return 100.0 * n / len(rows)


def dim_aggregate(
    rows: List[Dict[str, Any]], dim: str, *, equal_split: bool = True
) -> List[Dict[str, Any]]:
    """Aggregate tag -> keyword count, search volume (equal-split for multi-tags)."""
    tag_kw: Dict[str, set] = defaultdict(set)
    tag_vol: Dict[str, float] = defaultdict(float)
    tag_vols_list: Dict[str, List[float]] = defaultdict(list)

    for r in rows:
        tags = r.get(dim) or []
        if not tags:
            continue
        vol = float(r["搜索量"])
        share = vol / len(tags) if equal_split else vol
        for t in tags:
            tag_kw[t].add(r["关键词"])
            tag_vol[t] += share
            tag_vols_list[t].append(share)

    total_vol = sum(tag_vol.values()) or 1.0
    # Top keyword per tag (by full keyword volume among those carrying the tag)
    top_kw: Dict[str, Tuple[str, float]] = {}
    for r in rows:
        tags = r.get(dim) or []
        for t in tags:
            cur = top_kw.get(t)
            if cur is None or r["搜索量"] > cur[1]:
                top_kw[t] = (r["关键词"], r["搜索量"])

    out = []
    for t, kws in tag_kw.items():
        vols = tag_vols_list[t]
        med = statistics.median(vols) if vols else 0.0
        out.append({
            "维度": dim,
            "标签": t,
            "词数": len(kws),
            "搜索量": round(tag_vol[t], 2),
            "中位搜索量": round(med, 2),
            "占比": round(100.0 * tag_vol[t] / total_vol, 2),
            "Top词": top_kw.get(t, ("", 0))[0],
            "Top词搜索量": top_kw.get(t, ("", 0))[1],
        })
    out.sort(key=lambda x: (-x["搜索量"], -x["词数"], x["标签"]))
    return out


def head_tail_split(rows: List[Dict[str, Any]], head_pct: float = 4.0, tail_pct: float = 80.0):
    """Head = top head_pct% by volume; Tail = bottom tail_pct% by keyword count (lowest volume)."""
    sorted_rows = sorted(rows, key=lambda r: r["搜索量"], reverse=True)
    n = len(sorted_rows)
    if n == 0:
        return [], [], sorted_rows
    head_n = max(1, int(math.ceil(n * head_pct / 100.0)))
    tail_n = max(1, int(math.floor(n * tail_pct / 100.0)))
    head = sorted_rows[:head_n]
    # bottom by volume = reverse sorted take last tail_n
    tail = sorted_rows[-tail_n:] if tail_n < n else sorted_rows
    return head, tail, sorted_rows


def attr_distribution(subset: List[Dict[str, Any]], dim: str, top_n: int = 15) -> List[Dict[str, Any]]:
    return dim_aggregate(subset, dim)[:top_n]


def cooccurrence(
    rows: List[Dict[str, Any]], dim_a: str, dim_b: str, top_n: int = 20
) -> List[Dict[str, Any]]:
    pair_vol: Dict[Tuple[str, str], float] = defaultdict(float)
    pair_kw: Dict[Tuple[str, str], set] = defaultdict(set)
    for r in rows:
        ta = r.get(dim_a) or []
        tb = r.get(dim_b) or []
        if not ta or not tb:
            continue
        vol = float(r["搜索量"])
        denom = len(ta) * len(tb)
        share = vol / denom if denom else 0.0
        for a in ta:
            for b in tb:
                pair_vol[(a, b)] += share
                pair_kw[(a, b)].add(r["关键词"])
    items = [
        {
            "维A": dim_a,
            "标签A": a,
            "维B": dim_b,
            "标签B": b,
            "搜索量": round(v, 2),
            "词数": len(pair_kw[(a, b)]),
        }
        for (a, b), v in pair_vol.items()
    ]
    items.sort(key=lambda x: -x["搜索量"])
    return items[:top_n]


def blue_ocean_window(rows: List[Dict[str, Any]], top_n: int = 30) -> List[Dict[str, Any]]:
    """High volume + blue-ish competition."""
    blue_labels = {"蓝海", "温和", "blue", "mild", "low"}
    scored = []
    for r in rows:
        ocean = (r.get("蓝海度") or "").strip()
        vol = r["搜索量"]
        if vol <= 0:
            continue
        is_blue = any(b in ocean for b in blue_labels) or ocean in blue_labels
        # score: volume with boost for blue
        boost = 1.5 if is_blue else (1.2 if ocean in ("一般",) else 0.5)
        if not is_blue and ocean not in ("一般", "温和", "蓝海"):
            # still include high-volume mild only
            if ocean in ("激烈", "极激烈"):
                continue
        scored.append({
            "关键词": r["关键词"],
            "搜索量": vol,
            "蓝海度": ocean or "-",
            "竞品数": r.get("竞品数") or "",
            "推荐行动": r.get("推荐行动") or "",
            "score": vol * boost,
        })
    scored.sort(key=lambda x: -x["score"])
    return scored[:top_n]


def build_insights(rows: List[Dict[str, Any]], aggs: Dict[str, List], meta: Dict) -> List[str]:
    insights: List[str] = []
    n = len(rows)
    vols = sorted(r["搜索量"] for r in rows)
    total = sum(vols) or 1.0
    p50 = percentile(vols, 50)
    p90 = percentile(vols, 90)
    head, tail, sorted_rows = head_tail_split(rows, 4.0, 80.0)
    head_vol = sum(r["搜索量"] for r in head)
    head_share = 100.0 * head_vol / total
    head_n = len(head)
    tail_vol = sum(r["搜索量"] for r in tail)

    insights.append(
        f"共 {n} 个关键词，总搜索量 {int(total):,}；单词搜索量 P50={p50:.0f}、P90={p90:.0f}（长尾偏斜明显）。"
    )
    insights.append(
        f"头部流量（搜索量前 {head_n} 词 ≈ 前4%）：贡献总搜索量的 {head_share:.1f}%（{int(head_vol):,}），"
        f"头部集中度{'极高' if head_share >= 60 else '较高' if head_share >= 40 else '中等'}。"
    )
    insights.append(
        f"长尾（词量后80%，共 {len(tail)} 词）合计搜索量 {int(tail_vol):,}，"
        f"占总搜索量 {100.0 * tail_vol / total:.1f}%；共性见各维长尾分布。"
    )

    # fill rate warnings
    low_dims = []
    for d in ATTR_DIMS:
        fr = meta["fill_rates"].get(d, 0)
        if fr < 5.0:
            low_dims.append(f"{d}({fr:.1f}%)")
    if low_dims:
        insights.append(
            "填充率警告（<5%）：" + "、".join(low_dims) + " —— 这些维度当前不适合作为主战场，仅作弱信号参考。"
        )
    high_dims = sorted(
        ((d, meta["fill_rates"][d]) for d in ATTR_DIMS),
        key=lambda x: -x[1],
    )[:3]
    insights.append(
        "属性填充率最高三维："
        + "、".join(f"{d}({fr:.1f}%)" for d, fr in high_dims)
        + "，更适合作为主分析轴。"
    )

    # top tags in key dims
    for dim in ("目标人群", "功效", "产品形态", "风格属性", "痛点/需求", "修饰/价值", "产地/文化"):
        arr = aggs.get(dim) or []
        if not arr:
            continue
        top = arr[0]
        if top["搜索量"] <= 0:
            continue
        insights.append(
            f"「{dim}」头部标签「{top['标签']}」：词数 {top['词数']}，分摊搜索量 {int(top['搜索量']):,}（占该维 {top['占比']:.1f}%），Top词「{top['Top词']}」。"
        )

    # head commons
    head_commons = []
    for dim in ("产品形态", "风格属性", "功效", "通用/品类", "修饰/价值"):
        dist = attr_distribution(head, dim, 3)
        if dist:
            labels = "、".join(f"{x['标签']}({int(x['搜索量']):,})" for x in dist[:3])
            head_commons.append(f"{dim}: {labels}")
    if head_commons:
        insights.append("头部词属性共性 → " + "；".join(head_commons))

    # tail commons
    tail_commons = []
    for dim in ("产品形态", "风格属性", "功效", "通用/品类"):
        dist = attr_distribution(tail, dim, 3)
        if dist:
            labels = "、".join(f"{x['标签']}(词{x['词数']})" for x in dist[:3])
            tail_commons.append(f"{dim}: {labels}")
    if tail_commons:
        insights.append("长尾词属性共性 → " + "；".join(tail_commons))

    # cooccurrence highlights
    for pair in (("目标人群", "功效"), ("产品形态", "风格属性"), ("痛点/需求", "功效")):
        co = cooccurrence(rows, pair[0], pair[1], 3)
        if co:
            bits = "、".join(f"{c['标签A']}×{c['标签B']}({int(c['搜索量']):,})" for c in co[:3])
            insights.append(f"高量交叉「{pair[0]}×{pair[1]}」Top：{bits}")

    # blue ocean
    blue = blue_ocean_window(rows, 5)
    if blue:
        bits = "、".join(f"「{b['关键词']}」({int(b['搜索量']):,}/{b['蓝海度']})" for b in blue[:5])
        insights.append(f"高需求低竞争窗口（蓝海/温和优先）：{bits}")

    # audience coverage
    aud_n = sum(1 for r in rows if r.get("目标人群"))
    insights.append(
        f"人群覆盖率：{100.0 * aud_n / n:.1f}%（{aud_n}/{n}）；"
        + ("人群信号稀疏，投放/选品勿过度依赖人群维。" if aud_n / n < 0.05 else "可结合人群维做细分投放。")
    )

    return insights


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

def svg_bar(items: List[Tuple[str, float]], width: int = 560, bar_h: int = 18, gap: int = 6) -> str:
    if not items:
        return "<p class='muted'>暂无数据</p>"
    max_v = max(v for _, v in items) or 1.0
    label_w = 160
    chart_w = width - label_w - 70
    height = len(items) * (bar_h + gap) + 10
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" role="img">']
    for i, (label, val) in enumerate(items):
        y = i * (bar_h + gap) + 4
        bw = max(2, int(chart_w * (val / max_v)))
        safe = html.escape(label[:28] + ("…" if len(label) > 28 else ""))
        parts.append(
            f'<text x="0" y="{y + bar_h - 4}" font-size="12" fill="#334155">{safe}</text>'
            f'<rect x="{label_w}" y="{y}" width="{bw}" height="{bar_h}" rx="3" fill="#3b82f6" opacity="0.85"/>'
            f'<text x="{label_w + bw + 6}" y="{y + bar_h - 4}" font-size="11" fill="#64748b">{int(val):,}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def table_html(headers: List[str], rows: List[List[Any]], max_rows: int = 25) -> str:
    th = "".join(f"<th>{html.escape(str(h))}</th>" for h in headers)
    body = []
    for r in rows[:max_rows]:
        tds = "".join(f"<td>{html.escape(str(c))}</td>" for c in r)
        body.append(f"<tr>{tds}</tr>")
    more = ""
    if len(rows) > max_rows:
        more = f"<p class='muted'>仅展示前 {max_rows} 行，完整数据见 Excel。</p>"
    return f"<table><thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table>{more}"


def render_html(
    title: str,
    category: str,
    rows: List[Dict[str, Any]],
    aggs: Dict[str, List],
    insights: List[str],
    meta: Dict,
    head: List,
    tail: List,
) -> str:
    n = len(rows)
    total = meta["total_vol"]
    generated = datetime.now().strftime("%Y-%m-%d %H:%M CST")

    kpi_cards = f"""
    <div class="kpis">
      <div class="kpi"><div class="n">{n:,}</div><div class="l">关键词数</div></div>
      <div class="kpi"><div class="n">{int(total):,}</div><div class="l">总搜索量</div></div>
      <div class="kpi"><div class="n">{meta['audience_coverage']:.1f}%</div><div class="l">人群覆盖率</div></div>
      <div class="kpi"><div class="n">{meta['p50']:.0f} / {meta['p90']:.0f}</div><div class="l">搜索量 P50 / P90</div></div>
      <div class="kpi"><div class="n">{meta['head_share']:.1f}%</div><div class="l">头部4%词量贡献</div></div>
      <div class="kpi"><div class="n">{meta['fill_dims_ok']}</div><div class="l">填充率≥5%的维数</div></div>
    </div>
    """

    fill_rows = [[d, f"{meta['fill_rates'][d]:.1f}%", "⚠ 偏低" if meta["fill_rates"][d] < 5 else "可用"] for d in ATTR_DIMS]

    dim_sections = []
    for d in ATTR_DIMS:
        arr = aggs.get(d) or []
        fr = meta["fill_rates"][d]
        warn = " <span class='warn'>填充率偏低，勿作主战场</span>" if fr < 5 else ""
        bars = svg_bar([(x["标签"], x["搜索量"]) for x in arr[:12]])
        tbl = table_html(
            ["标签", "词数", "搜索量(等分)", "中位", "占比%", "Top词"],
            [[x["标签"], x["词数"], int(x["搜索量"]), x["中位搜索量"], x["占比"], x["Top词"]] for x in arr],
            20,
        )
        dim_sections.append(
            f"<section class='card'><h3>{html.escape(d)} <small>填充率 {fr:.1f}%{warn}</small></h3>"
            f"<div class='chart'>{bars}</div>{tbl}</section>"
        )

    # head/tail
    def subset_attr_block(name: str, subset: List[Dict], dims: Sequence[str]) -> str:
        blocks = []
        for d in dims:
            dist = attr_distribution(subset, d, 8)
            if not dist:
                continue
            bars = svg_bar([(x["标签"], x["搜索量"]) for x in dist[:8]], width=520)
            blocks.append(f"<h4>{html.escape(d)}</h4><div class='chart'>{bars}</div>")
        return f"<section class='card'><h3>{html.escape(name)}（n={len(subset)}）</h3>{''.join(blocks) or '<p class=muted>无属性命中</p>'}</section>"

    head_html = subset_attr_block(
        "头部流量共性（搜索量前4%）",
        head,
        ["产品形态", "风格属性", "功效", "通用/品类", "修饰/价值", "目标人群", "痛点/需求"],
    )
    tail_html = subset_attr_block(
        "长尾共性（词量后80%）",
        tail,
        ["产品形态", "风格属性", "功效", "通用/品类"],
    )

    # co-occurrence
    co_blocks = []
    for a, b in (("目标人群", "功效"), ("产品形态", "风格属性"), ("痛点/需求", "功效"), ("修饰/价值", "产品形态")):
        co = cooccurrence(rows, a, b, 15)
        if not co:
            continue
        tbl = table_html(
            ["标签A", "标签B", "分摊搜索量", "词数"],
            [[c["标签A"], c["标签B"], int(c["搜索量"]), c["词数"]] for c in co],
            15,
        )
        co_blocks.append(f"<h4>{html.escape(a)} × {html.escape(b)}</h4>{tbl}")

    blue = blue_ocean_window(rows, 25)
    blue_tbl = table_html(
        ["关键词", "搜索量", "蓝海度", "竞品数", "推荐行动"],
        [[b["关键词"], int(b["搜索量"]), b["蓝海度"], b["竞品数"], b["推荐行动"]] for b in blue],
        25,
    )

    insight_lis = "".join(f"<li>{html.escape(s)}</li>" for s in insights)

    css = """
    :root { --bg:#0f172a; --card:#1e293b; --text:#e2e8f0; --muted:#94a3b8; --accent:#38bdf8; --warn:#fbbf24; --ok:#4ade80; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
           background: linear-gradient(160deg,#0f172a,#1e293b 40%,#0f172a); color: var(--text); line-height:1.55; }
    header { padding: 28px 32px 12px; border-bottom: 1px solid #334155; }
    header h1 { margin:0 0 6px; font-size: 1.6rem; }
    header .meta { color: var(--muted); font-size: 0.9rem; }
    main { padding: 20px 32px 48px; max-width: 1100px; margin: 0 auto; }
    .kpis { display:grid; grid-template-columns: repeat(auto-fit,minmax(140px,1fr)); gap:12px; margin: 16px 0 24px; }
    .kpi { background: var(--card); border:1px solid #334155; border-radius:12px; padding:14px 16px; }
    .kpi .n { font-size:1.35rem; font-weight:700; color: var(--accent); }
    .kpi .l { font-size:0.8rem; color: var(--muted); margin-top:4px; }
    .card { background: var(--card); border:1px solid #334155; border-radius:14px; padding:18px 20px; margin: 18px 0; }
    h2 { margin: 28px 0 10px; font-size:1.25rem; border-left: 4px solid var(--accent); padding-left:10px; }
    h3 { margin: 0 0 12px; font-size:1.05rem; }
    h3 small { color: var(--muted); font-weight:400; }
    h4 { margin: 14px 0 8px; color:#cbd5e1; font-size:0.95rem; }
    table { width:100%; border-collapse: collapse; font-size:0.85rem; margin-top:8px; }
    th, td { border-bottom:1px solid #334155; padding:6px 8px; text-align:left; vertical-align:top; }
    th { color:#94a3b8; font-weight:600; background:#0f172a55; }
    .muted { color: var(--muted); font-size:0.85rem; }
    .warn { color: var(--warn); font-size:0.8rem; }
    .chart { overflow-x:auto; margin: 8px 0 12px; background:#0f172a66; border-radius:8px; padding:8px; }
    ul.insights li { margin: 8px 0; }
    footer { text-align:center; color:var(--muted); font-size:0.8rem; padding: 24px; }
    .note { background:#0f172a; border-left:3px solid var(--warn); padding:10px 14px; margin:12px 0; border-radius:6px; font-size:0.9rem; }
    """

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{html.escape(title)}</title>
<style>{css}</style>
</head>
<body>
<header>
  <h1>{html.escape(title)}</h1>
  <div class="meta">品类：{html.escape(category or "-")} · 生成时间：{generated} · 口径：多标签搜索量等分 · 源：COSMO 属性 CSV</div>
</header>
<main>
  <h2>1. 总览 KPI</h2>
  {kpi_cards}
  <div class="note">说明：属性多标签（如 a|b）在维度汇总时对搜索量做<strong>等分</strong>；未标注「-」不计入该维。数字均来自输入 CSV，未外推。</div>
  <section class="card">
    <h3>各维填充率</h3>
    {table_html(["维度", "填充率", "建议"], fill_rows, 20)}
  </section>

  <h2>2. 数学 / 科学洞察</h2>
  <section class="card">
    <ul class="insights">{insight_lis}</ul>
  </section>

  <h2>3. 头部 vs 长尾</h2>
  {head_html}
  {tail_html}

  <h2>4. 属性维度流量副表</h2>
  {"".join(dim_sections)}

  <h2>5. 维度交叉（共现）</h2>
  <section class="card">
    {"".join(co_blocks) or "<p class='muted'>有效交叉不足</p>"}
  </section>

  <h2>6. 蓝海 × 搜索量窗口</h2>
  <section class="card">
    <p class="muted">优先「蓝海/温和」且仍有搜索量的词；激烈/极激烈已排除。</p>
    {blue_tbl}
  </section>
</main>
<footer>COSMO 市场分析 · bailing-cosmo-market-analysis · 离线自包含 HTML（无 CDN）</footer>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Excel
# ---------------------------------------------------------------------------

THIN = Border(
    left=Side(style="thin", color="CBD5E1"),
    right=Side(style="thin", color="CBD5E1"),
    top=Side(style="thin", color="CBD5E1"),
    bottom=Side(style="thin", color="CBD5E1"),
)
HEADER_FILL = PatternFill("solid", fgColor="1E293B")
HEADER_FONT = Font(color="F8FAFC", bold=True)
SECTION_FILL = PatternFill("solid", fgColor="334155")


def _style_header(ws, ncols: int):
    for c in range(1, ncols + 1):
        cell = ws.cell(1, c)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", wrap_text=True)


def _autosize(ws, max_width: int = 42):
    for col in ws.columns:
        letter = get_column_letter(col[0].column)
        length = 0
        for cell in col[:80]:
            v = "" if cell.value is None else str(cell.value)
            length = max(length, min(len(v) + 2, max_width))
        ws.column_dimensions[letter].width = max(10, length)


def write_excel(
    path: Path,
    rows: List[Dict[str, Any]],
    aggs: Dict[str, List],
    insights: List[str],
    meta: Dict,
    title: str,
    category: str,
):
    wb = Workbook()

    # --- 说明 ---
    ws = wb.active
    ws.title = "说明"
    lines = [
        ("报告标题", title),
        ("品类", category or "-"),
        ("生成时间", datetime.now().strftime("%Y-%m-%d %H:%M CST")),
        ("词数", meta["n"]),
        ("总搜索量", int(meta["total_vol"])),
        ("人群覆盖率%", round(meta["audience_coverage"], 2)),
        ("P50 搜索量", meta["p50"]),
        ("P90 搜索量", meta["p90"]),
        ("头部4%词数", meta["head_n"]),
        ("头部贡献占比%", round(meta["head_share"], 2)),
        ("口径", "多标签（a|b）在维度汇总时搜索量等分；空/- 视为未标"),
        ("依赖", "输入为 bailing-cerebro-keyword-analysis 产出的 COSMO 属性 CSV"),
    ]
    ws.append(["字段", "值"])
    for a, b in lines:
        ws.append([a, b])
    _style_header(ws, 2)
    ws.append([])
    ws.append(["维度", "填充率%"])
    for d in ATTR_DIMS:
        ws.append([d, round(meta["fill_rates"][d], 2)])
    _autosize(ws)

    # --- 词明细 ---
    ws2 = wb.create_sheet("词明细")
    detail_headers = CORE_COLS + ATTR_DIMS
    ws2.append(detail_headers)
    for r in rows:
        row = []
        for c in CORE_COLS:
            if c == "搜索量":
                row.append(r["搜索量"])
            else:
                row.append(r.get(c, ""))
        for d in ATTR_DIMS:
            row.append(r.get(f"{d}__raw") or ("|".join(r.get(d) or []) if r.get(d) else "-"))
        ws2.append(row)
    _style_header(ws2, len(detail_headers))
    ws2.auto_filter.ref = f"A1:{get_column_letter(len(detail_headers))}{ws2.max_row}"
    ws2.freeze_panes = "C2"
    _autosize(ws2)

    # --- 维度汇总（全维合并） ---
    ws3 = wb.create_sheet("维度汇总")
    ws3.append(["维度", "标签", "词数", "搜索量(等分)", "中位搜索量", "占比%", "Top词", "Top词搜索量"])
    for d in ATTR_DIMS:
        for x in aggs.get(d) or []:
            ws3.append([x["维度"], x["标签"], x["词数"], x["搜索量"], x["中位搜索量"], x["占比"], x["Top词"], x["Top词搜索量"]])
    _style_header(ws3, 8)
    ws3.auto_filter.ref = f"A1:H{ws3.max_row}"
    ws3.freeze_panes = "C2"
    _autosize(ws3)

    # --- 副表汇总（分段） ---
    ws4 = wb.create_sheet("副表汇总")
    ws4.append(["段落", "维度", "标签", "词数", "搜索量(等分)", "占比%", "Top词"])
    section_map = {
        "人群汇总": ["目标人群"],
        "价值修饰": ["修饰/价值"],
        "功效": ["功效"],
        "形态": ["产品形态"],
        "风格": ["风格属性"],
        "痛点": ["痛点/需求"],
        "产地": ["产地/文化"],
        "场景节日": ["场景/活动", "季节/节日", "购买场所"],
        "材质部位": ["成分/材质", "使用部位"],
        "品类": ["通用/品类"],
    }
    for sec, dims in section_map.items():
        for d in dims:
            for x in aggs.get(d) or []:
                ws4.append([sec, d, x["标签"], x["词数"], x["搜索量"], x["占比"], x["Top词"]])
    _style_header(ws4, 7)
    ws4.auto_filter.ref = f"A1:G{ws4.max_row}"
    _autosize(ws4)

    # dedicated sheets for key dims (optional clarity)
    for sheet_name, dim in [
        ("人群汇总", "目标人群"),
        ("价值修饰", "修饰/价值"),
        ("功效", "功效"),
        ("形态", "产品形态"),
        ("风格", "风格属性"),
        ("痛点", "痛点/需求"),
        ("产地", "产地/文化"),
    ]:
        w = wb.create_sheet(sheet_name)
        w.append(["标签", "词数", "搜索量(等分)", "中位搜索量", "占比%", "Top词", "Top词搜索量"])
        for x in aggs.get(dim) or []:
            w.append([x["标签"], x["词数"], x["搜索量"], x["中位搜索量"], x["占比"], x["Top词"], x["Top词搜索量"]])
        _style_header(w, 7)
        if w.max_row > 1:
            w.auto_filter.ref = f"A1:G{w.max_row}"
        _autosize(w)

    # --- 洞察 ---
    ws5 = wb.create_sheet("洞察")
    ws5.append(["#", "结论"])
    for i, s in enumerate(insights, 1):
        ws5.append([i, s])
    _style_header(ws5, 2)
    ws5.column_dimensions["A"].width = 6
    ws5.column_dimensions["B"].width = 100
    for row in ws5.iter_rows(min_row=2, max_row=ws5.max_row, min_col=2, max_col=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    # --- 交叉 ---
    ws6 = wb.create_sheet("交叉共现")
    ws6.append(["维A", "标签A", "维B", "标签B", "分摊搜索量", "词数"])
    for a, b in (("目标人群", "功效"), ("产品形态", "风格属性"), ("痛点/需求", "功效"), ("修饰/价值", "产品形态")):
        for c in cooccurrence(rows, a, b, 30):
            ws6.append([c["维A"], c["标签A"], c["维B"], c["标签B"], c["搜索量"], c["词数"]])
    _style_header(ws6, 6)
    if ws6.max_row > 1:
        ws6.auto_filter.ref = f"A1:F{ws6.max_row}"
    _autosize(ws6)

    # --- 蓝海窗口 ---
    ws7 = wb.create_sheet("蓝海窗口")
    ws7.append(["关键词", "搜索量", "蓝海度", "竞品数", "推荐行动"])
    for b in blue_ocean_window(rows, 50):
        ws7.append([b["关键词"], b["搜索量"], b["蓝海度"], b["竞品数"], b["推荐行动"]])
    _style_header(ws7, 5)
    if ws7.max_row > 1:
        ws7.auto_filter.ref = f"A1:E{ws7.max_row}"
    _autosize(ws7)

    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


# ---------------------------------------------------------------------------
# Also write CSV summaries
# ---------------------------------------------------------------------------

def write_summary_csvs(out_dir: Path, aggs: Dict[str, List], insights: List[str]):
    # master dim summary
    path = out_dir / "cosmo-dim-summary.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["维度", "标签", "词数", "搜索量", "中位搜索量", "占比", "Top词", "Top词搜索量"],
        )
        w.writeheader()
        for d in ATTR_DIMS:
            for x in aggs.get(d) or []:
                w.writerow(x)
    insight_path = out_dir / "cosmo-insights.txt"
    insight_path.write_text("\n".join(f"{i}. {s}" for i, s in enumerate(insights, 1)), encoding="utf-8")
    return path, insight_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def analyze(rows: List[Dict[str, Any]]) -> Tuple[Dict, Dict[str, List], List, List, List[str]]:
    n = len(rows)
    vols = sorted(r["搜索量"] for r in rows)
    total = sum(vols)
    fill_rates = {d: fill_rate(rows, d) for d in ATTR_DIMS}
    aud_n = sum(1 for r in rows if r.get("目标人群"))
    head, tail, _ = head_tail_split(rows, 4.0, 80.0)
    head_vol = sum(r["搜索量"] for r in head)
    meta = {
        "n": n,
        "total_vol": total,
        "p50": percentile(vols, 50) if vols else 0,
        "p90": percentile(vols, 90) if vols else 0,
        "fill_rates": fill_rates,
        "audience_coverage": 100.0 * aud_n / n if n else 0,
        "head_n": len(head),
        "head_share": 100.0 * head_vol / total if total else 0,
        "fill_dims_ok": sum(1 for d in ATTR_DIMS if fill_rates[d] >= 5.0),
    }
    aggs = {d: dim_aggregate(rows, d) for d in ATTR_DIMS}
    insights = build_insights(rows, aggs, meta)
    return meta, aggs, head, tail, insights


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="COSMO 市场分析：CSV → HTML + Excel")
    ap.add_argument("--input", "-i", required=True, help="COSMO 属性 CSV 路径")
    ap.add_argument("--output-dir", "-o", required=True, help="输出目录")
    ap.add_argument("--title", default="COSMO 市场分析报告")
    ap.add_argument("--category", default="")
    args = ap.parse_args(argv)

    inp = Path(args.input).expanduser().resolve()
    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not inp.exists():
        raise SystemExit(f"输入不存在: {inp}")

    rows, colmap, _ = load_rows(inp)
    if not rows:
        raise SystemExit("CSV 无有效关键词行")

    meta, aggs, head, tail, insights = analyze(rows)

    slug = re.sub(r"[^\w\-]+", "-", (args.category or "cosmo").strip())[:40] or "cosmo"
    html_path = out_dir / f"cosmo-market-report-{slug}.html"
    xlsx_path = out_dir / f"cosmo-market-workbook-{slug}.xlsx"
    # also a filtered-friendly keyword csv copy summary is in workbook; export dim csv
    kw_csv = out_dir / f"cosmo-keyword-detail-{slug}.csv"

    html_body = render_html(args.title, args.category, rows, aggs, insights, meta, head, tail)
    html_path.write_text(html_body, encoding="utf-8")

    write_excel(xlsx_path, rows, aggs, insights, meta, args.title, args.category)

    # keyword detail csv
    with kw_csv.open("w", encoding="utf-8-sig", newline="") as f:
        headers = CORE_COLS + ATTR_DIMS
        w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            row = {c: r.get(c, "") for c in CORE_COLS}
            for d in ATTR_DIMS:
                row[d] = r.get(f"{d}__raw") or ("|".join(r.get(d) or []) if r.get(d) else "-")
            w.writerow(row)

    dim_csv, insight_txt = write_summary_csvs(out_dir, aggs, insights)

    # print summary for agent
    print("=== COSMO Market Analysis Done ===")
    print(f"input: {inp}")
    print(f"keywords: {meta['n']}")
    print(f"total_volume: {int(meta['total_vol'])}")
    print(f"P50/P90: {meta['p50']:.0f}/{meta['p90']:.0f}")
    print(f"head4%_share: {meta['head_share']:.2f}%")
    print(f"audience_coverage: {meta['audience_coverage']:.2f}%")
    print(f"HTML: {html_path} ({html_path.stat().st_size} bytes)")
    print(f"XLSX: {xlsx_path} ({xlsx_path.stat().st_size} bytes)")
    print(f"CSV_detail: {kw_csv}")
    print(f"CSV_dim: {dim_csv}")
    print(f"insights: {insight_txt}")
    print("--- Top insights ---")
    for i, s in enumerate(insights[:8], 1):
        print(f"{i}. {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
