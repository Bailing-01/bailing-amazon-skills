#!/usr/bin/env python3
"""
ABA 品牌视图搜索查询绩效 — 确定性加工链 (S2-S4) 统一脚道

输入:
  argv[1] = JSON 字符串, 格式: {"file_paths":"path1,path2,...","brand":"YTDB"}
  - file_paths: 1-4 个 CSV 文件路径, 逗号分隔. 最新周放第一个.
  - brand: 品牌名 (选填, 从 CSV 元信息自动检测)

输出:
  JSON 到 stdout, 包含:
  - overview:      最新周大盘 vs 品牌漏斗汇总 (对象)
  - pareto:       帕累托 80/20 分析 (对象)
  - head_gaps:    最新周头部 10 词 CTR/Conv Gap 明细 (数组)
  - tail_categories: 最新周长尾词 6 大意图分类统计 (数组)
  - price_segments:  最新周 5 价位段深度分析 (数组)
  - weekly_trend:  多周漏斗率/份额趋势 + 关键词流动 (数组, 单周时为空)
  - keyword_tags_csv: 31 列标签表 CSV 文件路径 (字符串)

依赖:
  - linkfox_paths.resolve_data_path() 用于 keyword_tags CSV 落盘
  - 无第三方依赖, 仅用标准库

用法:
  python scripts/run_pipeline.py '{"file_paths":"a.csv,b.csv","brand":"YTDB"}'
  # 或经 response_io.py 封装:
  python scripts/response_io.py run --script scripts/run_pipeline.py --out-dir <dir> '{"file_paths":"...","brand":"..."}'
"""

import csv
import json
import os
import sys
import time
from collections import defaultdict

# ---------------------------------------------------------------------------
# linkfox_paths — 同目录引用
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import linkfox_paths  # noqa: E402


# ---------------------------------------------------------------------------
# CSV 解析 — 统一 parse_csv, 合并 4 个参考脚本的字段提取
# ---------------------------------------------------------------------------

def _safe_int(v):
    try:
        return int(v) if v else 0
    except (ValueError, TypeError):
        return 0


def _safe_float(v):
    try:
        return float(v) if v else 0.0
    except (ValueError, TypeError):
        return 0.0


def parse_csv(file_path):
    """读取 ABA 品牌视图 CSV, 返回 (rows, meta_string).

    每行 dict 包含全链路字段 + 衍生品牌量/率.
    """
    rows = []
    meta = ""
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        # 第 1 行: 元信息 (品牌名 + 报告周期)
        meta_row = next(reader, None)
        meta = meta_row[0] if meta_row else ""

        # 第 2 行: 列头
        header = next(reader, None)
        if not header:
            return rows, meta

        col_map = {}
        for i, h in enumerate(header):
            col_map[h.strip()] = i

        idx = {
            "query": col_map.get("搜索查询", 0),
            "search_volume": col_map.get("搜索查询量", 2),
            "impressions_total": col_map.get("曝光：曝光总量", 3),
            "impressions_brand_share": col_map.get("曝光: 品牌曝光占比 %", 5),
            "clicks_total": col_map.get("点击量：总次数", 6),
            "clicks_brand_share": col_map.get("点击量：品牌点击占比 %", 9),
            "clicks_price_median": col_map.get("点击量：价格(中位数)", 10),
            "clicks_brand_price": col_map.get("点击量：品牌售价（中位数）", 11),
            "clicks_same_day": col_map.get("点击量：当日达配送速度", 12),
            "clicks_1day": col_map.get("点击量：1 天配送速度", 13),
            "clicks_2day": col_map.get("点击：2天配送速度", 14),
            "cart_total": col_map.get("购物车添加：总数", 15),
            "cart_brand_share": col_map.get("购物车添加：品牌份额 %", 18),
            "cart_price_median": col_map.get("加入购物车：售价（中位数）", 19),
            "cart_brand_price": col_map.get("购物车添加：品牌价格（中位数）", 20),
            "purchases_total": col_map.get("购买：下单总数", 24),
            "purchases_brand_share": col_map.get("购买次数：品牌份额 %", 27),
            "purch_price_median": col_map.get("购买次数：价格（中位数）", 28),
            "brand_purch_price": col_map.get("购买次数：品牌价格（中位数）", 29),
            "report_date": col_map.get("报告日期", 33),
        }

        for row in reader:
            if not row or not row[0]:
                continue
            r = {
                "query": row[idx["query"]].strip().strip('"'),
                "search_volume": _safe_int(row[idx["search_volume"]]),
                "impressions_total": _safe_int(row[idx["impressions_total"]]),
                "impressions_brand_share": _safe_float(row[idx["impressions_brand_share"]]),
                "clicks_total": _safe_int(row[idx["clicks_total"]]),
                "clicks_brand_share": _safe_float(row[idx["clicks_brand_share"]]),
                "clicks_price_median": _safe_float(row[idx["clicks_price_median"]]),
                "clicks_brand_price": _safe_float(row[idx["clicks_brand_price"]]),
                "clicks_same_day": _safe_int(row[idx["clicks_same_day"]]),
                "clicks_1day": _safe_int(row[idx["clicks_1day"]]),
                "clicks_2day": _safe_int(row[idx["clicks_2day"]]),
                "cart_total": _safe_int(row[idx["cart_total"]]),
                "cart_brand_share": _safe_float(row[idx["cart_brand_share"]]),
                "cart_price_median": _safe_float(row[idx["cart_price_median"]]),
                "cart_brand_price": _safe_float(row[idx["cart_brand_price"]]),
                "purchases_total": _safe_int(row[idx["purchases_total"]]),
                "purchases_brand_share": _safe_float(row[idx["purchases_brand_share"]]),
                "purch_price_median": _safe_float(row[idx["purch_price_median"]]),
                "brand_purch_price": _safe_float(row[idx["brand_purch_price"]]),
                "report_date": row[idx["report_date"]] if idx["report_date"] < len(row) else "",
            }
            # 衍生品牌量
            r["brand_impr"] = int(r["impressions_total"] * r["impressions_brand_share"] / 100)
            r["brand_clicks"] = int(r["clicks_total"] * r["clicks_brand_share"] / 100)
            r["brand_cart"] = int(r["cart_total"] * r["cart_brand_share"] / 100)
            r["brand_purch"] = int(r["purchases_total"] * r["purchases_brand_share"] / 100)
            # 衍生率
            r["mkt_ctr"] = r["clicks_total"] / r["impressions_total"] * 100 if r["impressions_total"] else 0
            r["mkt_cart_rate"] = r["cart_total"] / r["clicks_total"] * 100 if r["clicks_total"] else 0
            r["mkt_conv"] = r["purchases_total"] / r["clicks_total"] * 100 if r["clicks_total"] else 0
            r["mkt_cart_conv"] = r["purchases_total"] / r["cart_total"] * 100 if r["cart_total"] else 0
            r["brand_ctr"] = r["brand_clicks"] / r["brand_impr"] * 100 if r["brand_impr"] else 0
            r["brand_cart_rate"] = r["brand_cart"] / r["brand_clicks"] * 100 if r["brand_clicks"] else 0
            r["brand_conv"] = r["brand_purch"] / r["brand_clicks"] * 100 if r["brand_clicks"] else 0
            r["brand_cart_conv"] = r["brand_purch"] / r["brand_cart"] * 100 if r["brand_cart"] else 0
            rows.append(r)
    return rows, meta


# ---------------------------------------------------------------------------
# S2: 漏斗汇总 + 帕累托
# ---------------------------------------------------------------------------

def calc_weekly_overview(rows):
    """计算大盘 vs 品牌漏斗汇总, 返回 overview dict."""
    total = defaultdict(int)
    brand = defaultdict(int)
    for r in rows:
        total["impressions"] += r["impressions_total"]
        total["clicks"] += r["clicks_total"]
        total["cart"] += r["cart_total"]
        total["purchases"] += r["purchases_total"]
        brand["impressions"] += r["brand_impr"]
        brand["clicks"] += r["brand_clicks"]
        brand["cart"] += r["brand_cart"]
        brand["purchases"] += r["brand_purch"]

    m_ctr = total["clicks"] / total["impressions"] * 100 if total["impressions"] else 0
    m_cart_rate = total["cart"] / total["clicks"] * 100 if total["clicks"] else 0
    m_conv = total["purchases"] / total["clicks"] * 100 if total["clicks"] else 0
    m_cart_conv = total["purchases"] / total["cart"] * 100 if total["cart"] else 0
    b_ctr = brand["clicks"] / brand["impressions"] * 100 if brand["impressions"] else 0
    b_cart_rate = brand["cart"] / brand["clicks"] * 100 if brand["clicks"] else 0
    b_conv = brand["purchases"] / brand["clicks"] * 100 if brand["clicks"] else 0
    b_cart_conv = brand["purchases"] / brand["cart"] * 100 if brand["cart"] else 0

    # 配送速度
    m_same = sum(r["clicks_same_day"] for r in rows)
    m_1day = sum(r["clicks_1day"] for r in rows)
    m_2day = sum(r["clicks_2day"] for r in rows)
    b_same = sum(int(r["clicks_same_day"] * r["clicks_brand_share"] / 100) for r in rows)
    b_1day = sum(int(r["clicks_1day"] * r["clicks_brand_share"] / 100) for r in rows)
    b_2day = sum(int(r["clicks_2day"] * r["clicks_brand_share"] / 100) for r in rows)

    # 品牌均价
    prices_brand = [r["clicks_brand_price"] for r in rows if 5 < r["clicks_brand_price"] < 100]
    prices_market = [r["clicks_price_median"] for r in rows if 5 < r["clicks_price_median"] < 100]

    return {
        "total_queries": len(rows),
        "market_impressions": total["impressions"],
        "market_clicks": total["clicks"],
        "market_cart": total["cart"],
        "market_purchases": total["purchases"],
        "market_ctr": round(m_ctr, 2),
        "market_cart_rate": round(m_cart_rate, 2),
        "market_conv": round(m_conv, 2),
        "market_cart_conv": round(m_cart_conv, 2),
        "brand_impressions": brand["impressions"],
        "brand_clicks": brand["clicks"],
        "brand_cart": brand["cart"],
        "brand_purchases": brand["purchases"],
        "brand_ctr": round(b_ctr, 2),
        "brand_cart_rate": round(b_cart_rate, 2),
        "brand_conv": round(b_conv, 2),
        "brand_cart_conv": round(b_cart_conv, 2),
        "impr_share": round(brand["impressions"] / total["impressions"] * 100, 2) if total["impressions"] else 0,
        "click_share": round(brand["clicks"] / total["clicks"] * 100, 2) if total["clicks"] else 0,
        "cart_share": round(brand["cart"] / total["cart"] * 100, 2) if total["cart"] else 0,
        "purch_share": round(brand["purchases"] / total["purchases"] * 100, 2) if total["purchases"] else 0,
        "brand_same_day_pct": round(b_same / brand["clicks"] * 100, 2) if brand["clicks"] else 0,
        "brand_1day_pct": round(b_1day / brand["clicks"] * 100, 2) if brand["clicks"] else 0,
        "brand_2day_pct": round(b_2day / brand["clicks"] * 100, 2) if brand["clicks"] else 0,
        "market_same_day_pct": round(m_same / total["clicks"] * 100, 2) if total["clicks"] else 0,
        "market_1day_pct": round(m_1day / total["clicks"] * 100, 2) if total["clicks"] else 0,
        "market_2day_pct": round(m_2day / total["clicks"] * 100, 2) if total["clicks"] else 0,
        "brand_avg_price": round(sum(prices_brand) / len(prices_brand), 2) if prices_brand else 0,
        "market_avg_price": round(sum(prices_market) / len(prices_market), 2) if prices_market else 0,
    }


def calc_pareto(rows):
    """帕累托 80/20 分析: 按品牌曝光降序, 找 80% 累计切分点."""
    sorted_rows = sorted(rows, key=lambda x: x["brand_impr"], reverse=True)
    total_brand_impr = sum(r["brand_impr"] for r in sorted_rows)
    total_brand_clicks = sum(r["brand_clicks"] for r in sorted_rows)
    total_brand_purch = sum(r["brand_purch"] for r in sorted_rows)

    cumulative = 0
    pareto_idx = len(sorted_rows)  # 默认全部
    for i, r in enumerate(sorted_rows):
        cumulative += r["brand_impr"]
        if total_brand_impr and cumulative / total_brand_impr >= 0.8:
            pareto_idx = i + 1
            break

    head = sorted_rows[:pareto_idx]
    tail = sorted_rows[pareto_idx:]

    def _agg(rs):
        return {
            "count": len(rs),
            "brand_impressions": sum(r["brand_impr"] for r in rs),
            "brand_clicks": sum(r["brand_clicks"] for r in rs),
            "brand_purchases": sum(r["brand_purch"] for r in rs),
            "brand_ctr": round(
                sum(r["brand_clicks"] for r in rs) / max(sum(r["brand_impr"] for r in rs), 1) * 100, 2
            ) if any(r["brand_impr"] for r in rs) else 0,
            "brand_conv": round(
                sum(r["brand_purch"] for r in rs) / max(sum(r["brand_clicks"] for r in rs), 1) * 100, 2
            ) if any(r["brand_clicks"] for r in rs) else 0,
        }

    return {
        "total_queries": len(rows),
        "pareto_cut": pareto_idx,
        "head": _agg(head),
        "tail": _agg(tail),
        "head_pct": round(pareto_idx / len(rows) * 100, 1) if rows else 0,
        "head_impr_pct": round(
            sum(r["brand_impr"] for r in head) / max(total_brand_impr, 1) * 100, 1
        ),
        "head_clicks_pct": round(
            sum(r["brand_clicks"] for r in head) / max(total_brand_clicks, 1) * 100, 1
        ),
        "head_purch_pct": round(
            sum(r["brand_purch"] for r in head) / max(total_brand_purch, 1) * 100, 1
        ),
        "top10_queries": [
            {
                "query": r["query"],
                "brand_impr": r["brand_impr"],
                "brand_clicks": r["brand_clicks"],
                "brand_purch": r["brand_purch"],
                "brand_ctr": round(r["brand_ctr"], 2),
                "brand_conv": round(r["brand_conv"], 2),
                "impr_share": r["impressions_brand_share"],
                "click_share": r["clicks_brand_share"],
                "purch_share": r["purchases_brand_share"],
            }
            for r in sorted_rows[:10]
        ],
    }


# ---------------------------------------------------------------------------
# S3: 头部差距 + 长尾分类 + 价位段
# ---------------------------------------------------------------------------

def calc_head_gaps(rows):
    """按品牌曝光降序取头部 10 词, 逐词计算 CTR Gap 和 Conv Gap."""
    sorted_rows = sorted(rows, key=lambda x: x["brand_impr"], reverse=True)
    head_gaps = []
    for r in sorted_rows[:10]:
        head_gaps.append({
            "query": r["query"],
            "brand_impr": r["brand_impr"],
            "total_impr": r["impressions_total"],
            "impr_share": r["impressions_brand_share"],
            "brand_clicks": r["brand_clicks"],
            "total_clicks": r["clicks_total"],
            "click_share": r["clicks_brand_share"],
            "brand_ctr": round(r["brand_ctr"], 2),
            "mkt_ctr": round(r["mkt_ctr"], 2),
            "ctr_gap": round(r["brand_ctr"] - r["mkt_ctr"], 2),
            "brand_purch": r["brand_purch"],
            "total_purch": r["purchases_total"],
            "purch_share": r["purchases_brand_share"],
            "brand_conv": round(r["brand_conv"], 2),
            "mkt_conv": round(r["mkt_conv"], 2),
            "conv_gap": round(r["brand_conv"] - r["mkt_conv"], 2),
            "brand_price": r["clicks_brand_price"],
            "mkt_price": r["clicks_price_median"],
        })
    return head_gaps


def calc_tail_categories(rows):
    """长尾词 (头部 10 词之后) 按 6 大搜索意图分类归组."""
    sorted_rows = sorted(rows, key=lambda x: x["brand_impr"], reverse=True)
    tail = sorted_rows[10:]

    categories = {
        "bleaching_whitening": {
            "label": "漂白/美白类",
            "keywords": ["bleach", "whitening", "lightening", "bleaching", "blanqueador", "aclarador"],
        },
        "neck_firming": {
            "label": "颈部紧致类",
            "keywords": ["neck", "firming", "tighten", "turkey", "cuello", "papada", "reafirmante"],
        },
        "underarm_intimate": {
            "label": "腋下/私密部位类",
            "keywords": ["underarm", "armpit", "axilas", "intimate", "bikini", "private", "partes"],
        },
        "body_skin": {
            "label": "身体/皮肤类",
            "keywords": ["body", "skin", "cuerpo", "piel", "dark", "hyperpigmentation"],
        },
        "competitor_brand": {
            "label": "竞品品牌词",
            "keywords": [
                "sally hansen", "jolen", "gold bond", "roc", "strivectin",
                "eucerin", "go pure", "porcelana", "murad", "olay",
                "routine wellness", "dekliderm", "agelyss", "cetaphil",
            ],
        },
        "spanish": {
            "label": "西语搜索词",
            "keywords": [
                "crema", "para", "axilas", "cuello", "papada", "reafirmante",
                "antiarrugas", "blanqueadora", "aclarante", "aclarador",
                "despigmentante", "entrepierna",
            ],
        },
    }

    cat_stats = defaultdict(
        lambda: {
            "count": 0,
            "brand_impr": 0,
            "brand_clicks": 0,
            "brand_purch": 0,
            "total_impr": 0,
            "total_clicks": 0,
            "total_purch": 0,
            "queries": [],
        }
    )

    for r in tail:
        q_lower = r["query"].lower()
        matched = False
        for cat, info in categories.items():
            if any(kw in q_lower for kw in info["keywords"]):
                cs = cat_stats[cat]
                cs["count"] += 1
                cs["brand_impr"] += r["brand_impr"]
                cs["brand_clicks"] += r["brand_clicks"]
                cs["brand_purch"] += r["brand_purch"]
                cs["total_impr"] += r["impressions_total"]
                cs["total_clicks"] += r["clicks_total"]
                cs["total_purch"] += r["purchases_total"]
                if len(cs["queries"]) < 5:
                    cs["queries"].append(r["query"])
                matched = True
                break
        if not matched:
            cs = cat_stats["other"]
            cs["count"] += 1
            cs["brand_impr"] += r["brand_impr"]
            cs["brand_clicks"] += r["brand_clicks"]
            cs["brand_purch"] += r["brand_purch"]
            cs["total_impr"] += r["impressions_total"]
            cs["total_clicks"] += r["clicks_total"]
            cs["total_purch"] += r["purchases_total"]
            if len(cs["queries"]) < 5:
                cs["queries"].append(r["query"])

    tail_categories = []
    for cat, info in categories.items():
        cs = cat_stats[cat]
        if cs["count"] == 0:
            continue
        b_ctr = cs["brand_clicks"] / cs["brand_impr"] * 100 if cs["brand_impr"] else 0
        m_ctr = cs["total_clicks"] / cs["total_impr"] * 100 if cs["total_impr"] else 0
        b_conv = cs["brand_purch"] / cs["brand_clicks"] * 100 if cs["brand_clicks"] else 0
        m_conv = cs["total_purch"] / cs["total_clicks"] * 100 if cs["total_clicks"] else 0
        tail_categories.append({
            "category": cat,
            "label": info["label"],
            "count": cs["count"],
            "brand_impr": cs["brand_impr"],
            "brand_clicks": cs["brand_clicks"],
            "brand_purch": cs["brand_purch"],
            "brand_ctr": round(b_ctr, 2),
            "mkt_ctr": round(m_ctr, 2),
            "ctr_gap": round(b_ctr - m_ctr, 2),
            "brand_conv": round(b_conv, 2),
            "mkt_conv": round(m_conv, 2),
            "conv_gap": round(b_conv - m_conv, 2),
            "sample_queries": cs["queries"],
        })

    # other
    cs = cat_stats["other"]
    if cs["count"] > 0:
        b_ctr = cs["brand_clicks"] / cs["brand_impr"] * 100 if cs["brand_impr"] else 0
        m_ctr = cs["total_clicks"] / cs["total_impr"] * 100 if cs["total_impr"] else 0
        b_conv = cs["brand_purch"] / cs["brand_clicks"] * 100 if cs["brand_clicks"] else 0
        m_conv = cs["total_purch"] / cs["total_clicks"] * 100 if cs["total_clicks"] else 0
        tail_categories.append({
            "category": "other",
            "label": "其他",
            "count": cs["count"],
            "brand_impr": cs["brand_impr"],
            "brand_clicks": cs["brand_clicks"],
            "brand_purch": cs["brand_purch"],
            "brand_ctr": round(b_ctr, 2),
            "mkt_ctr": round(m_ctr, 2),
            "ctr_gap": round(b_ctr - m_ctr, 2),
            "brand_conv": round(b_conv, 2),
            "mkt_conv": round(m_conv, 2),
            "conv_gap": round(b_conv - m_conv, 2),
            "sample_queries": cs["queries"],
        })

    tail_categories.sort(key=lambda x: x["brand_impr"], reverse=True)
    return tail_categories


def calc_price_segments(rows):
    """按大盘价格中位数分 5 段, 分析各段品牌 vs 大盘表现."""
    valid = [r for r in rows if 1 < r["clicks_price_median"] < 500]
    segments = [
        {"name": "低价段", "label": "低价 ($1-8)", "min": 1, "max": 8, "color": "#06b6d4"},
        {"name": "中低段", "label": "中低 ($8-15)", "min": 8, "max": 15, "color": "#4f46e5"},
        {"name": "中价段", "label": "中价 ($15-25)", "min": 15, "max": 25, "color": "#8b5cf6"},
        {"name": "中高段", "label": "中高 ($25-40)", "min": 25, "max": 40, "color": "#f59e0b"},
        {"name": "高价段", "label": "高价 ($40+)", "min": 40, "max": 500, "color": "#ef4444"},
    ]

    results = []
    for seg in segments:
        seg_rows = [r for r in valid if seg["min"] <= r["clicks_price_median"] < seg["max"]]
        total_clicks = sum(r["clicks_total"] for r in seg_rows)
        total_purch = sum(r["purchases_total"] for r in seg_rows)
        brand_clicks = sum(r["brand_clicks"] for r in seg_rows)
        brand_purch = sum(r["brand_purch"] for r in seg_rows)
        brand_impr = sum(r["brand_impr"] for r in seg_rows)
        total_impr = sum(r["impressions_total"] for r in seg_rows)

        m_ctr = total_clicks / total_impr * 100 if total_impr else 0
        m_conv = total_purch / total_clicks * 100 if total_clicks else 0
        b_ctr = brand_clicks / brand_impr * 100 if brand_impr else 0
        b_conv = brand_purch / brand_clicks * 100 if brand_clicks else 0

        brand_prices = [r["clicks_brand_price"] for r in seg_rows if 1 < r["clicks_brand_price"] < 500]
        market_prices = [r["clicks_price_median"] for r in seg_rows]
        avg_brand_price = sum(brand_prices) / len(brand_prices) if brand_prices else 0
        avg_market_price = sum(market_prices) / len(market_prices) if market_prices else 0

        brand_purch_prices = [r["brand_purch_price"] for r in seg_rows if 1 < r["brand_purch_price"] < 500]
        market_purch_prices = [r["purch_price_median"] for r in seg_rows if 1 < r["purch_price_median"] < 500]
        avg_brand_purch = sum(brand_purch_prices) / len(brand_purch_prices) if brand_purch_prices else 0
        avg_market_purch = sum(market_purch_prices) / len(market_purch_prices) if market_purch_prices else 0

        top_kw = sorted(seg_rows, key=lambda x: x["purchases_total"], reverse=True)[:10]
        brand_purch_kw = sorted(
            [r for r in seg_rows if r["brand_purch"] > 0],
            key=lambda x: x["brand_purch"],
            reverse=True,
        )[:10]

        results.append({
            "name": seg["name"],
            "label": seg["label"],
            "color": seg["color"],
            "query_count": len(seg_rows),
            "total_impressions": total_impr,
            "total_clicks": total_clicks,
            "total_purchases": total_purch,
            "brand_impressions": brand_impr,
            "brand_clicks": brand_clicks,
            "brand_purchases": brand_purch,
            "market_ctr": round(m_ctr, 2),
            "market_conv": round(m_conv, 2),
            "brand_ctr": round(b_ctr, 2),
            "brand_conv": round(b_conv, 2),
            "impr_share": round(brand_impr / total_impr * 100, 2) if total_impr else 0,
            "click_share": round(brand_clicks / total_clicks * 100, 2) if total_clicks else 0,
            "purch_share": round(brand_purch / total_purch * 100, 2) if total_purch else 0,
            "avg_market_price": round(avg_market_price, 2),
            "avg_brand_price": round(avg_brand_price, 2),
            "avg_market_purch_price": round(avg_market_purch, 2),
            "avg_brand_purch_price": round(avg_brand_purch, 2),
            "top_keywords": [
                {
                    "query": r["query"],
                    "price": r["clicks_price_median"],
                    "brand_price": r["clicks_brand_price"],
                    "total_purch": r["purchases_total"],
                    "brand_purch": r["brand_purch"],
                    "market_conv": round(r["purchases_total"] / r["clicks_total"] * 100, 2) if r["clicks_total"] else 0,
                }
                for r in top_kw
            ],
            "brand_purch_keywords": [
                {
                    "query": r["query"],
                    "price": r["clicks_price_median"],
                    "brand_price": r["clicks_brand_price"],
                    "brand_purch": r["brand_purch"],
                    "brand_clicks": r["brand_clicks"],
                    "brand_conv": round(r["brand_purch"] / r["brand_clicks"] * 100, 2) if r["brand_clicks"] else 0,
                }
                for r in brand_purch_kw
            ],
        })
    return results


# ---------------------------------------------------------------------------
# S4: 多周趋势 + 标签表 CSV
# ---------------------------------------------------------------------------

def calc_weekly_trend(weekly_data):
    """多周趋势: 每周 overview + 关键词流动.

    weekly_data: [(week_label, date_range, rows), ...] 按时间正序 (最旧 -> 最新)
    返回 weekly_trend 数组.
    """
    if len(weekly_data) < 2:
        return []

    weekly = []
    all_queries = {}  # query -> {week_label -> per-query data}

    for week_label, date_range, rows in weekly_data:
        ov = calc_weekly_overview(rows)
        ov["week"] = week_label
        ov["date_range"] = date_range
        weekly.append(ov)

        for r in rows:
            q = r["query"]
            if q not in all_queries:
                all_queries[q] = {}
            all_queries[q][week_label] = {
                "brand_impressions": r["brand_impr"],
                "brand_clicks": r["brand_clicks"],
                "brand_purchases": r["brand_purch"],
                "total_impressions": r["impressions_total"],
                "total_clicks": r["clicks_total"],
                "total_purchases": r["purchases_total"],
            }

    # 关键词流动: 最旧周 vs 最新周
    oldest_week = weekly_data[0][0]
    newest_week = weekly_data[-1][0]
    new_keywords = [q for q in all_queries if newest_week in all_queries[q] and oldest_week not in all_queries[q]]
    lost_keywords = [q for q in all_queries if oldest_week in all_queries[q] and newest_week not in all_queries[q]]

    # 关键词趋势 top20 (按总购买量)
    keyword_trends = []
    for q, weeks in all_queries.items():
        purch_vals = [weeks.get(wl, {}).get("brand_purchases", 0) for wl, _, _ in weekly_data]
        total_purch = sum(purch_vals)
        oldest_impr = weeks.get(oldest_week, {}).get("brand_impressions", 0)
        newest_impr = weeks.get(newest_week, {}).get("brand_impressions", 0)
        impr_change = newest_impr - oldest_impr

        if total_purch > 0 or newest_impr > 50:
            oldest_purch = weeks.get(oldest_week, {}).get("brand_purchases", 0)
            newest_purch = weeks.get(newest_week, {}).get("brand_purchases", 0)
            trend = "up" if newest_purch > oldest_purch else ("down" if newest_purch < oldest_purch and oldest_purch > 0 else "flat")
            keyword_trends.append({
                "query": q,
                "total_purch": total_purch,
                "oldest_impr": oldest_impr,
                "newest_impr": newest_impr,
                "impr_change": impr_change,
                "impr_change_pct": round(impr_change / oldest_impr * 100, 1) if oldest_impr else 0,
                "trend": trend,
            })

    keyword_trends.sort(key=lambda x: x["total_purch"], reverse=True)

    return {
        "weekly_overview": weekly,
        "keyword_trends_top20": keyword_trends[:20],
        "new_keywords_count": len(new_keywords),
        "lost_keywords_count": len(lost_keywords),
        "new_keywords_sample": new_keywords[:15],
        "lost_keywords_sample": lost_keywords[:15],
        "total_unique_keywords": len(all_queries),
    }


# ---------------------------------------------------------------------------
# 标签表 CSV 生成
# ---------------------------------------------------------------------------

def _tag_price_segment(price):
    if price < 8:
        return "低价($1-8)"
    elif price < 15:
        return "中低($8-15)"
    elif price < 25:
        return "中价($15-25)"
    elif price < 40:
        return "中高($25-40)"
    else:
        return "高价($40+)"


def _tag_share(share):
    if share >= 2.0:
        return "高"
    elif share >= 0.5:
        return "中"
    else:
        return "低"


def _tag_rate(brand_rate, market_rate):
    """比较品牌率 vs 大盘率, 返回 高/中/低 标签."""
    if brand_rate == 0 and market_rate == 0:
        return "-"
    gap = brand_rate - market_rate
    if gap > 0.5:
        return "高"
    elif gap < -0.5:
        return "低"
    else:
        return "中"


def generate_keyword_tags_csv(rows, ts=None):
    """对最新周每条搜索词打 31 列标签, 输出 CSV 到会话 data 目录, 返回路径."""
    if ts is None:
        ts = time.time()

    output_rows = []
    for r in rows:
        b_impr = r["brand_impr"]
        b_clicks = r["brand_clicks"]
        b_cart = r["brand_cart"]
        b_purch = r["brand_purch"]

        # GMV
        market_gmv = (
            r["purch_price_median"] * r["purchases_total"]
            if 0 < r["purch_price_median"] < 500
            else 0
        )
        brand_gmv = (
            r["brand_purch_price"] * b_purch
            if 0 < r["brand_purch_price"] < 500
            else 0
        )

        # 大盘率
        m_ctr = r["mkt_ctr"]
        m_cart_rate = r["mkt_cart_rate"]
        m_conv = r["mkt_conv"]

        # 品牌率
        b_ctr = r["brand_ctr"]
        b_cart_rate = r["brand_cart_rate"]
        b_conv = r["brand_conv"]

        # 价位段标签
        price_tag = _tag_price_segment(r["clicks_price_median"]) if r["clicks_price_median"] > 0 else "未标注"

        # 份额标签
        impr_tag = _tag_share(r["impressions_brand_share"])
        click_tag = _tag_share(r["clicks_brand_share"])
        cart_tag = _tag_share(r["cart_brand_share"])
        purch_tag = _tag_share(r["purchases_brand_share"])

        # 率标签
        ctr_tag = _tag_rate(b_ctr, m_ctr)
        cart_rate_tag = _tag_rate(b_cart_rate, m_cart_rate)
        conv_tag = _tag_rate(b_conv, m_conv)

        output_rows.append({
            "搜索词": r["query"],
            "大盘GMV": round(market_gmv, 2),
            "品牌GMV": round(brand_gmv, 2),
            "大盘曝光": r["impressions_total"],
            "品牌曝光": b_impr,
            "曝光份额%": r["impressions_brand_share"],
            "曝光标签": impr_tag,
            "大盘点击": r["clicks_total"],
            "品牌点击": b_clicks,
            "点击份额%": r["clicks_brand_share"],
            "点击标签": click_tag,
            "品牌CTR%": round(b_ctr, 2),
            "大盘CTR%": round(m_ctr, 2),
            "CTR标签": ctr_tag,
            "大盘加购": r["cart_total"],
            "品牌加购": b_cart,
            "加购份额%": r["cart_brand_share"],
            "加购标签": cart_tag,
            "品牌加购率%": round(b_cart_rate, 2),
            "大盘加购率%": round(m_cart_rate, 2),
            "加购率标签": cart_rate_tag,
            "大盘购买": r["purchases_total"],
            "品牌购买": b_purch,
            "购买份额%": r["purchases_brand_share"],
            "购买标签": purch_tag,
            "品牌转化率%": round(b_conv, 2),
            "大盘转化率%": round(m_conv, 2),
            "转化标签": conv_tag,
            "价位段": price_tag,
            "大盘均价": r["clicks_price_median"],
            "品牌均价": r["clicks_brand_price"],
        })

    # 按品牌曝光降序
    output_rows.sort(key=lambda x: x["品牌曝光"], reverse=True)

    # 落盘到会话 data 目录
    csv_path = linkfox_paths.resolve_data_path("aba-keyword-tags", ts, ext="csv")

    fieldnames = list(output_rows[0].keys()) if output_rows else []
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in output_rows:
            writer.writerow(row)

    return csv_path


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def _extract_week_info(meta, file_path):
    """从 CSV 元信息行提取周次标签和日期范围.

    meta 示例: "YTDB, 2026-08-09~2026-08-15, 搜索查询绩效, ..."
    若无法解析, 用文件名 + report_date 回退.
    """
    week_label = ""
    date_range = ""

    if meta:
        parts = [p.strip() for p in meta.split(",")]
        # 尝试找到日期范围部分 (含 ~)
        for p in parts:
            if "~" in p:
                date_range = p
                # 提取周序号
                try:
                    start_date = p.split("~")[0].strip()
                    # 尝试从日期推算 ISO 周序号
                    import datetime as _dt
                    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"):
                        try:
                            d = _dt.datetime.strptime(start_date, fmt)
                            week_label = f"周{d.isocalendar()[1]}"
                            break
                        except ValueError:
                            continue
                except Exception:
                    pass
                if not week_label:
                    week_label = date_range
                break

    if not week_label:
        # 回退: 用文件名
        basename = os.path.basename(file_path)
        week_label = basename[:20]
        date_range = basename

    return week_label, date_range


def main():
    # 解析参数
    if len(sys.argv) < 2:
        print(json.dumps({"error": "缺少参数: JSON 字符串 {\"file_paths\":\"...\",\"brand\":\"...\"}"}, ensure_ascii=False))
        sys.exit(1)

    try:
        params = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"参数 JSON 解析失败: {e}"}, ensure_ascii=False))
        sys.exit(1)

    file_paths_str = params.get("file_paths", "")
    brand = params.get("brand", "")

    if not file_paths_str:
        print(json.dumps({"error": "缺少 file_paths 参数"}, ensure_ascii=False))
        sys.exit(1)

    file_paths = [p.strip() for p in file_paths_str.split(",") if p.strip()]
    if len(file_paths) > 4:
        print(json.dumps({"error": "最多支持 4 个 CSV 文件"}, ensure_ascii=False))
        sys.exit(1)

    # 读取所有 CSV (file_paths[0] = 最新周)
    weekly_data = []  # [(week_label, date_range, rows), ...]
    all_metas = []

    for i, fpath in enumerate(file_paths):
        if not os.path.isfile(fpath):
            print(json.dumps({"error": f"CSV 文件不存在: {fpath}"}, ensure_ascii=False))
            sys.exit(1)
        rows, meta = parse_csv(fpath)
        week_label, date_range = _extract_week_info(meta, fpath)
        # 如果无法从 meta 提取, 用序号
        if not week_label:
            week_label = f"周{len(file_paths) - i}"
        if not date_range:
            date_range = week_label
        weekly_data.append((week_label, date_range, rows))
        all_metas.append(meta)

        if i == 0 and not brand:
            # 尝试从元信息提取品牌名
            if meta:
                parts = [p.strip() for p in meta.split(",")]
                if parts:
                    brand = parts[0]

    # 最新周数据 (file_paths[0])
    latest_rows = weekly_data[0][2]

    # S2: 漏斗汇总 + 帕累托 (最新周)
    overview = calc_weekly_overview(latest_rows)
    overview["brand"] = brand
    overview["week"] = weekly_data[0][0]
    overview["date_range"] = weekly_data[0][1]

    pareto = calc_pareto(latest_rows)

    # S3: 头部差距 + 长尾分类 + 价位段 (最新周)
    head_gaps = calc_head_gaps(latest_rows)
    tail_categories = calc_tail_categories(latest_rows)
    price_segments = calc_price_segments(latest_rows)

    # S4: 多周趋势
    # weekly_data 按 file_paths 顺序 (最新 -> 最旧), 趋势需要正序 (最旧 -> 最新)
    if len(weekly_data) >= 2:
        trend_data = list(reversed(weekly_data))  # 最旧 -> 最新
        weekly_trend = calc_weekly_trend(trend_data)
    else:
        weekly_trend = []

    # 标签表 CSV (最新周)
    ts = time.time()
    keyword_tags_csv = generate_keyword_tags_csv(latest_rows, ts)

    # 组装输出
    result = {
        "overview": overview,
        "pareto": pareto,
        "head_gaps": head_gaps,
        "tail_categories": tail_categories,
        "price_segments": price_segments,
        "weekly_trend": weekly_trend,
        "keyword_tags_csv": keyword_tags_csv,
        "meta": {
            "brand": brand,
            "file_count": len(file_paths),
            "weeks": [{"week": wl, "date_range": dr, "query_count": len(rs)} for wl, dr, rs in weekly_data],
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(ts)),
        },
    }

    print(json.dumps(result, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
