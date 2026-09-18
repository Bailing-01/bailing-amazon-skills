#!/usr/bin/env python3
"""Scan text for terms in the local forbidden-term lexicon; no network access."""
import argparse, csv, re, sys
from pathlib import Path
FIELDS=["term","category","lang","severity","count","snippet"]
def read_text(path):
    return sys.stdin.read() if path in (None,"-") else Path(path).read_text(encoding="utf-8-sig")
def main():
    here=Path(__file__).resolve().parent
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("text",nargs="?",help="UTF-8 text file; omit or use - for stdin")
    p.add_argument("--lexicon",default=str(here.parent/"lexicon"/"forbidden_terms.csv"))
    a=p.parse_args(); text=read_text(a.text); out=csv.writer(sys.stdout,lineterminator="\n"); out.writerow(FIELDS)
    with open(a.lexicon,encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            term=(r.get("term") or "").strip()
            if not term: continue
            flags=re.IGNORECASE if any(ord(c)<128 and c.isalpha() for c in term) else 0
            ms=list(re.finditer(re.escape(term),text,flags))
            if not ms: continue
            snippets=[]
            for m in ms[:3]:
                snippets.append(" ".join(text[max(0,m.start()-35):min(len(text),m.end()+35)].split()))
            out.writerow([term,r.get("category(义成/冒器/药品/其他)",""),r.get("lang(en/zh)",""),r.get("severity",""),len(ms)," | ".join(snippets)])
if __name__=="__main__": main()
