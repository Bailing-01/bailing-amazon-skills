#!/usr/bin/env python3
"""
Westmonth.com Inventory Check Script
Queries SKU stock quantities on westmonth.com US site (delivery_region_id=3).

Two-step API:
1. Search: GET https://api-x.westmonth.com/product-center/shop/products/load-list?indistinct={SKU}&page=1&size=5
2. Detail: GET https://api-x.westmonth.com/product-center/shop/products/detail?product_id={id}&delivery_region_id=5
   -> Extract delivery_region_id=3 (US) qty from skus[].delivery_regions

Usage:
  python check_inventory.py --sku "ZP-A01-0007-01"
  python check_inventory.py --sku "SKU1,SKU2,SKU3"
  python check_inventory.py --sku-file /path/to/skus.txt
"""

import argparse
import json
import os
import sys
import time
import ssl
import urllib.request
from datetime import datetime
from pathlib import Path

# ── linkfox_paths (copied from _shared) ──────────────────────────────
# Resolve session directory for output
def _resolve_output_path(filename, subdir="data"):
    """Resolve output path under session directory."""
    session_id = os.environ.get("SESSION_ID", "")
    cwd = os.environ.get("ACPX_WORKSPACES") or os.getcwd()

    # Try cwd first
    root = Path(cwd)
    session_dir = root / "linkfox" / datetime.now().strftime("%Y-%m-%d") / session_id
    if not session_id:
        session_dir = root / "linkfox" / datetime.now().strftime("%Y-%m-%d") / f"{datetime.now().strftime('%H%M%S')}"

    out_dir = session_dir / subdir
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Fallback to home
        home = Path.home()
        session_dir = home / "linkfox" / datetime.now().strftime("%Y-%m-%d") / session_id or "default"
        out_dir = session_dir / subdir
        out_dir.mkdir(parents=True, exist_ok=True)

    return str(out_dir / filename)

# ── API Configuration ───────────────────────────────────────────────
SEARCH_API = "https://api-x.westmonth.com/product-center/shop/products/load-list"
DETAIL_API = "https://api-x.westmonth.com/product-center/shop/products/detail"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://westmonth.com/',
}

# SSL context (relaxed for API calls)
_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE

# Region IDs
US_REGION_ID = 3   # 美国
CN_REGION_ID = 5   # 中国
EU_REGION_ID = 14  # 欧盟


def fetch_json(url):
    """Fetch JSON from URL with standard headers."""
    req = urllib.request.Request(url)
    for k, v in HEADERS.items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, context=_ctx, timeout=20) as resp:
        return json.loads(resp.read().decode('utf-8'))


def search_sku(sku):
    """Step 1: Search for product_id by SKU using load-list API."""
    url = f"{SEARCH_API}?indistinct={urllib.parse.quote(sku)}&page=1&size=5"
    data = fetch_json(url)
    items = data.get('data', {}).get('data', [])

    # Find exact SKU match
    for item in items:
        if item.get('product_sku', '').upper() == sku.upper():
            return item
    # Fallback to first result
    return items[0] if items else None


def get_product_detail(product_id):
    """Step 2: Get product detail with delivery_regions stock info."""
    url = f"{DETAIL_API}?product_id={product_id}&delivery_region_id={CN_REGION_ID}"
    data = fetch_json(url)
    return data.get('data', {})


def extract_stock_quantity(detail_data, target_sku):
    """Extract US stock quantity from product detail's skus.delivery_regions."""
    skus = detail_data.get('skus', [])

    for sku_item in skus:
        sku_code = sku_item.get('sku', '').upper()
        if sku_code == target_sku.upper() or len(skus) == 1:
            delivery_regions = sku_item.get('delivery_regions', {})
            overall_qty = sku_item.get('quantity', 0)

            us_qty = None
            cn_qty = None
            eu_qty = None
            all_regions = {}

            for region_key, region_data in delivery_regions.items():
                region_name = region_data.get('delivery_region_name', '')
                qty = region_data.get('qty', 0)
                stock_text = region_data.get('stock_text', '')
                region_did = region_data.get('delivery_region_id', '')

                all_regions[region_name] = {
                    'delivery_region_id': region_did,
                    'qty': qty,
                    'stock_text': stock_text,
                }

                if region_did == US_REGION_ID or '美国' in region_name:
                    us_qty = qty
                elif region_did == CN_REGION_ID or '中国' in region_name:
                    cn_qty = qty
                elif region_did == EU_REGION_ID or '欧盟' in region_name:
                    eu_qty = qty

            return {
                'us_stock_qty': us_qty,
                'cn_stock_qty': cn_qty,
                'eu_stock_qty': eu_qty,
                'overall_qty': overall_qty,
                'all_regions': all_regions,
            }

    return {
        'us_stock_qty': None,
        'cn_stock_qty': None,
        'eu_stock_qty': None,
        'overall_qty': 0,
        'all_regions': {},
    }


def determine_status(us_qty):
    """Determine stock status from US quantity."""
    if us_qty is None:
        return '无美国站数据'
    try:
        qty = int(us_qty) if not isinstance(us_qty, int) else us_qty
        if qty > 0:
            return '有货'
        elif qty == 0:
            return '缺货'
        elif qty == 99999:
            return '充足'
        else:
            return '有货'
    except (ValueError, TypeError):
        return '未知'


def check_single_sku(sku):
    """Check inventory for a single SKU. Returns result dict."""
    # Step 1: Search
    try:
        matched = search_sku(sku)
    except Exception as e:
        return {
            'sku': sku,
            'status': '查询失败',
            'error': str(e),
            'us_stock_qty': None,
            'product_name': '',
            'product_id': None,
            'product_url': '',
        }

    if not matched:
        return {
            'sku': sku,
            'status': '未找到',
            'error': '',
            'us_stock_qty': None,
            'product_name': '',
            'product_id': None,
            'product_url': '',
        }

    product_id = matched.get('product_id')
    product_name = matched.get('product_name', '')
    product_url = matched.get('product_url', '')
    stock_status = matched.get('stock_status', '')
    shelf_status = matched.get('shelf_status', 0)
    active = matched.get('active', False)
    month_sale = matched.get('month_sale', 0)

    # Step 2: Detail
    try:
        detail = get_product_detail(product_id)
    except Exception as e:
        return {
            'sku': sku,
            'status': f'详情查询失败: {e}',
            'error': str(e),
            'us_stock_qty': None,
            'product_name': product_name,
            'product_id': product_id,
            'product_url': product_url,
        }

    # Step 3: Extract stock
    stock_info = extract_stock_quantity(detail, sku)
    us_qty = stock_info['us_stock_qty']
    status = determine_status(us_qty)

    return {
        'sku': sku,
        'status': status,
        'error': '',
        'us_stock_qty': us_qty,
        'cn_stock_qty': stock_info['cn_stock_qty'],
        'eu_stock_qty': stock_info['eu_stock_qty'],
        'overall_qty': stock_info['overall_qty'],
        'all_regions': stock_info['all_regions'],
        'product_name': product_name,
        'product_id': product_id,
        'product_url': product_url,
        'stock_status_from_list': stock_status,
        'shelf_status': shelf_status,
        'active': active,
        'month_sale': month_sale,
    }


def main():
    parser = argparse.ArgumentParser(description='Check westmonth.com US inventory for SKUs')
    parser.add_argument('--sku', help='SKU code(s), comma-separated for multiple')
    parser.add_argument('--sku-file', help='File with one SKU per line')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests (seconds)')
    args = parser.parse_args()

    # Parse SKUs
    skus = []
    if args.sku_file:
        with open(args.sku_file, 'r') as f:
            skus = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    elif args.sku:
        skus = [s.strip() for s in args.sku.split(',') if s.strip()]
    else:
        print("Error: --sku or --sku-file required", file=sys.stderr)
        sys.exit(1)

    if not skus:
        print("Error: no SKUs provided", file=sys.stderr)
        sys.exit(1)

    # Check each SKU
    results = []
    for i, sku in enumerate(skus):
        result = check_single_sku(sku)
        results.append(result)

        us_qty = result.get('us_stock_qty', 'N/A')
        status = result.get('status', 'N/A')
        name = result.get('product_name', '')[:40]
        print(f"[{i+1}/{len(skus)}] {sku} -> US: {us_qty} ({status}) | {name}", file=sys.stderr)

        if i < len(skus) - 1:
            time.sleep(args.delay)

    # Build output
    output = {
        'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'site': 'https://westmonth.com/',
        'target_region': f'美国 (delivery_region_id={US_REGION_ID})',
        'total_skus': len(skus),
        'results': results,
    }

    # Save JSON
    timestamp = int(datetime.now().timestamp() * 1000)
    filename = f"linkfox-westmonth-inventory-{timestamp}.json"
    output_path = _resolve_output_path(filename)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    file_size = os.path.getsize(output_path)

    # Summary
    in_stock = sum(1 for r in results if r['status'] in ['有货', '充足'])
    out_of_stock = sum(1 for r in results if r['status'] == '缺货')
    not_found = sum(1 for r in results if r['status'] == '未找到')
    no_data = sum(1 for r in results if r['status'] == '无美国站数据')

    print(f"\n=== Summary ===", file=sys.stderr)
    print(f"Total: {len(skus)} | In stock: {in_stock} | Out of stock: {out_of_stock} | Not found: {not_found} | No US data: {no_data}", file=sys.stderr)

    # Protocol output
    print(f"Saved full response: {output_path} ({file_size} bytes)")


if __name__ == '__main__':
    import urllib.parse
    main()
