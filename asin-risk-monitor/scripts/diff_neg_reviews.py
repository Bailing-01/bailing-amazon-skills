#!/usr/bin/env python3
"""Compare two neg_reviews CSV snapshots and print sampled new negatives."""
import argparse,csv
OUT=["asin","marketplace","old_date","new_date","new_review_ids","new_neg_count_delta","delta_1star","delta_2star","source_note"]
def load(path,asin):
    d={}
    with open(path,encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            if (r.get("asin","").strip()==asin): d[(r.get("marketplace","").strip(),asin)]=r
    return d
def num(r,k):
    try: return float((r.get(k) or "").strip())
    except (TypeError,ValueError): return None
def ids(r):
    return {x.strip() for x in (r.get("review_ids_sample") or "").replace("|",";").replace(",",";").split(";") if x.strip() and x.strip()!="无数据"}
def fmt(n):
    if n is None:return "无数据"
    return str(int(n)) if n.is_integer() else str(n)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("old_csv");p.add_argument("new_csv");p.add_argument("--asin",required=True);a=p.parse_args()
    old,new=load(a.old_csv,a.asin),load(a.new_csv,a.asin); w=csv.writer(__import__('sys').stdout,lineterminator="\n");w.writerow(OUT)
    for (market,asin),nr in sorted(new.items()):
        o=old.get((market,asin),{}); di=sorted(ids(nr)-ids(o)); nc=num(nr,"new_neg_since_yesterday"); count=len(di) if di else (max(0,int(nc)) if nc is not None else None)
        a1,b1=num(nr,"neg_count_1star"),num(o,"neg_count_1star");a2,b2=num(nr,"neg_count_2star"),num(o,"neg_count_2star")
        w.writerow([asin,market,o.get("date",""),nr.get("date",""),";".join(di) or "无数据",fmt(count),fmt(None if a1 is None or b1 is None else a1-b1),fmt(None if a2 is None or b2 is None else a2-b2),nr.get("note","")])
if __name__=="__main__":main()
