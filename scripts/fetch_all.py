#!/usr/bin/env python3
"""Bulk crawl zakon.kg KoP + GK articles into data/all_laws.json
Run: py scripts/fetch_all.py  (200 KoP + 60 GK = ~260 articles)
Resumable: skips already saved IDs.
"""
import json, re, ssl, time, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "all_laws.json"
CBD_KOP = "https://cbd.minjust.gov.kg/3-36/edition/60031/ru"
CBD_GK = "https://cbd.minjust.gov.kg/5/edition/57490/ru"
CTX = ssl._create_unverified_context()

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=10, context=CTX).read().decode("utf-8", "ignore")
    html = re.sub(r'<script.*?</script>', '', html, flags=re.S)
    html = re.sub(r'<style.*?</style>', '', html, flags=re.S)
    txt = re.sub(r'<[^>]+>', ' ', html)
    txt = ' '.join(txt.split())
    # title: Статья N. Title (2026)
    m = re.search(r'Статья\s+([\d\-]+)\s+(.+?)\s+\(2026\)', txt)
    title = m.group(2).strip() if m else ""
    # body: after breadcrumb РАЗДЕЛ / Глава ... up to "Просмотрено" or foot
    idx = txt.find("РАЗДЕЛ")
    if idx < 0: idx = 0
    # find end: after body there is footer text — cut at most 2000 chars
    body = txt[idx: idx+2200]
    # cut tail junk
    for marker in ["← Назад", "Поделиться", "Похожие", "Комментарии"]:
        if marker in body:
            body = body[:body.find(marker)]
    return title, body.strip()

def crawl(code, prefix, ids, cbd, existing):
    for art in ids:
        key = f"{prefix}{art}"
        if key in existing:
            print(f"skip {key}"); continue
        url = f"https://zakon.kg/law/{code}/st-{art}/"
        try:
            title, body = fetch(url)
            if not body:
                print(f"empty {key}"); continue
            existing[key] = {"id": key, "title": f"{code} ст.{art} {title}"[:180], "article": f"{code} ст.{art}", "text": body[:1800], "source_url": url, "cbd_url": cbd, "edition": "09.10.2026"}
            print(f"ok {key} {title[:50]}")
        except Exception as e:
            print(f"ERR {key} {e}")
        time.sleep(0.15)
        OUT.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    existing = {}
    if OUT.exists():
        try: existing = json.loads(OUT.read_text(encoding="utf-8"))
        except: existing = {}
    # KoP FULL: 1-700 (real last ~600), GK2 FULL: 415-1150
    kop_ids = list(range(1, 701))
    crawl("kop-kr", "kop_st", kop_ids, CBD_KOP, existing)
    gk_ids = list(range(415, 1151))
    crawl("gk-kr-2", "gk_st", gk_ids, CBD_GK, existing)
    print(f"DONE total {len(existing)} -> {OUT}")
