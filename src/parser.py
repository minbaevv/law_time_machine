#!/usr/bin/env python3
"""REAL parser: fetch zakon.kg article pages (mirror of cbd.minjust.gov.kg).
CBD returns 403 for direct fetch, so zakon.kg is used with citation to CBD edition.
Usage:
  py parser.py check-st-187
  py parser.py fetch kop-kr st-187
Saves to data/laws.json ONLY after manual verify (prints text, does not overwrite).
"""
import re, sys, urllib.request

BASE = "https://zakon.kg/law"
EDITION = {"kop-kr": "https://cbd.minjust.gov.kg/3-36/edition/60031/ru", "gk-kr-2": "https://cbd.minjust.gov.kg/5/edition/57490/ru"}

def fetch(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 LawTM/1.0"})
    try:
        html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Fetch failed for {url}: {e}")
        print("Fallback: open URL manually in browser (read tool works) and paste text. Do NOT auto-overwrite laws.json.")
        return ""
    html = re.sub(r'<script.*?</script>', '', html, flags=re.S)
    html = re.sub(r'<style.*?</style>', '', html, flags=re.S)
    text = re.sub(r'<[^>]+>', '\n', html)
    text = re.sub(r'\n+', '\n', text)
    return text

if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "check-st-187":
        print(fetch(f"{BASE}/kop-kr/st-187/")[:3000])
    elif len(sys.argv) >= 4 and sys.argv[1] == "fetch":
        code, art = sys.argv[2], sys.argv[3]
        txt = fetch(f"{BASE}/{code}/{art}/")
        print(f"CBD edition: {EDITION.get(code)}")
        print(txt[:5000])
    else:
        print("fetch kop-kr st-187 | fetch gk-kr-2 st-545")
