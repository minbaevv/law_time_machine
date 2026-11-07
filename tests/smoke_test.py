#!/usr/bin/env python3
"""Smoke test REAL: verify real articles, search, time note, checklist."""
import json, threading, urllib.request
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from app import H
from http.server import HTTPServer

def get(path):
    with urllib.request.urlopen(f"http://127.0.0.1:8766{path}", timeout=5) as r:
        ct = r.headers.get_content_type()
        data = r.read()
        try: return r.status, json.loads(data.decode())
        except: return r.status, data.decode()

def main():
    srv = HTTPServer(("127.0.0.1", 8766), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        s, d = get("/api/health"); assert d["ok"] and "Not legal advice" in d["disclaimer"], d; print("PASS health real")
        s, d = get("/api/laws?year=2026"); assert s == 200 and len(d["results"]) >= 25 and "КоП" in d["edition_note"], d; print("PASS laws 2026 count", len(d["results"]))
        s, d = get("/api/search?q=" + "%D1%81%D0%BA%D0%BE%D1%80%D0%BE%D1%81%D1%82%D1%8C"); assert s == 200 and any("187" in str(x) for x in d["hits"]), d; print("PASS search speed hits", len(d["hits"]))
        s, d = get("/api/search?q=" + "%D0%B7%D0%B0%D1%80%D0%BF%D0%BB%D0%B0%D1%82"); assert len(d["hits"]) >= 1, d; print("PASS search salary")
        s, d = get("/api/compare?topic_id=kop_st31"); assert "Штраф" in d["topic"]["title"], d; print("PASS compare art31")
        s, d = get("/api/scenarios"); assert len(d["scenarios"]) == 5, d; print("PASS scenarios 5")
        s, d = get("/api/simulate?id=speed_real"); assert "187" in str(d["scenario"]["articles"]), d; print("PASS simulate real articles")
        s, d = get("/api/answer?id=speed_real&step=0&pick=1"); assert d["correct"] is True, d; print("PASS answer")
        s, d = get("/api/checklist?id=speed_real"); assert "Протокол" in d, d; print("PASS checklist txt")
        print("ALL REAL PASS")
    finally:
        srv.shutdown()

if __name__ == "__main__":
    main()
