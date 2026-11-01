#!/usr/bin/env python3
"""Small auditable model; all defaults are teaching examples, not market data."""
import argparse
import json


def model(cost, referral, tacos, prices, baseline):
    if cost < 0 or not 0 <= referral < 1 or not 0 <= tacos < 1 or referral + tacos >= 1:
        raise ValueError('Require cost >= 0 and 0 <= referral + tacos < 1')
    if baseline <= 0 or any(p <= 0 for p in prices):
        raise ValueError('Prices and baseline must be positive')
    keep = 1 - referral - tacos
    base_profit = baseline * keep - cost
    rows = []
    for price in prices:
        profit = price * keep - cost
        rows.append(dict(price=price, unit_profit=round(profit, 6),
                         margin=round(profit / price, 6),
                         required_volume_multiple=(round(base_profit / profit, 6)
                                                   if profit > 1e-9 and base_profit > 0 else None)))
    return dict(teaching_example=True, cost=cost, referral=referral, tacos=tacos,
                break_even_price=round(cost / keep, 6), baseline_price=baseline,
                scope='Profit after listed costs only; not a demand model or final net profit', rows=rows)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cost', type=float, default=12.75)
    p.add_argument('--referral', type=float, default=.15)
    p.add_argument('--tacos', type=float, default=0)
    p.add_argument('--baseline', type=float, default=20)
    p.add_argument('--prices', type=float, nargs='+', default=[13, 14, 15, 15.2, 16, 18, 20])
    a = p.parse_args()
    try:
        print(json.dumps(model(a.cost, a.referral, a.tacos, a.prices, a.baseline), indent=2))
    except ValueError as e:
        p.error(str(e))
