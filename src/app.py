#!/usr/bin/env python3
"""KanunTime — production server (stdlib, threaded).
Sources: КоП 09.10.2026 (60031), ГК 28.07.2026 via zakon.kg mirror. Verify in CBD. Not legal advice.
Run dev:  py src/app.py
Run prod: HOST=0.0.0.0 PORT=8765 py src/app.py
"""
import json, os, sys, logging
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
try:
    from ai import ask_claude, health as ai_health
except Exception:
    try:
        from src.ai import ask_claude, health as ai_health
    except Exception:
        def ask_claude(q, h): return None
        def ai_health(): return {"model": "claude-haiku-4-5-20251001", "configured": False}

ROOT = Path(__file__).resolve().parent.parent
DATA_LAWS = ROOT / "data" / "laws.json"
DATA_SC = ROOT / "data" / "scenarios.json"
STATIC = ROOT / "static"
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8765"))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("kanuntime")

def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))

def time_note(year: int):
    if year < 2019:
        return "В этот год действовал КоАП 1998 (утратил 01.01.2019). КоП только с 2019. Штрафы и статьи не сравнимы напрямую. По КоП ст.3 — применяй закон времени деяния."
    if year < 2021:
        return "Переходный период: КоП действовал с 2019, но редакция 2021 ещё не была. Сверяй ст.187/193 редакции 2019-2021."
    return "Действует КоП 2021 №128, редакция 09.10.2026. Ст.3: за деяние — закон времени деяния."

class H(BaseHTTPRequestHandler):
    server_version = "KanunTime/1.0"
    def log_message(self, *a): pass
    def _headers(self, ctype, length, extra=None):
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(length))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline'; img-src 'self' data:; style-src 'self' 'unsafe-inline'")
        self.send_header("Referrer-Policy", "no-referrer")
        if extra:
            for k, v in extra.items(): self.send_header(k, v)
    def _json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status); self._headers("application/json; charset=utf-8", len(body)); self.end_headers()
        self.wfile.write(body); log.info("%s %s %d", self.command, self.path, status)
    def do_GET(self):
        u = urlparse(self.path); q = parse_qs(u.query)
        try:
            if u.path == "/health" or u.path == "/api/health":
                return self._json({"ok": True, "app": "law_time_machine", "disclaimer": "Not legal advice. Verify in CBD minjust.", "built": datetime.now(timezone.utc).isoformat()})
            if u.path == "/" or u.path == "/index.html" or u.path == "/chat" or u.path == "/chat.html":
                f = STATIC / ("chat.html" if u.path in ("/chat", "/chat.html") else "index.html")
                if not f.exists(): return self._json({"error": "no index"}, 404)
                body = f.read_bytes()
                self.send_response(200); self._headers("text/html; charset=utf-8", len(body)); self.end_headers(); self.wfile.write(body)
                log.info("GET / 200"); return
            if u.path == "/chat" or u.path == "/chat.html":
                f = STATIC / "chat.html"
                return self._serve(f)
            if u.path.startswith("/static/"):
                safe = Path(u.path).name
                f = STATIC / safe
                if f.exists():
                    body = f.read_bytes()
                    ctype = "image/svg+xml" if safe.endswith(".svg") else "application/octet-stream"
                    self.send_response(200); self._headers(ctype, len(body)); self.end_headers(); self.wfile.write(body)
                    log.info("GET static 200"); return
                return self._json({"error": "not found"}, 404)
            if u.path == "/api/laws":
                data = load_json(DATA_LAWS); year = int(q.get("year", ["2026"])[0])
                out = []
                for t in data["topics"]:
                    for v in t["versions"]:
                        if v["valid_from"] <= f"{year}-01-01" <= v["valid_to"] or (year >= 2021 and v["year"] == 2026):
                            out.append({"topic_id": t["id"], "title": t["title"], **v}); break
                return self._json({"year": year, "results": out, "disclaimer": data["disclaimer"], "time_note": time_note(year), "edition_note": data.get("edition_note")})
            if u.path == "/api/compare":
                data = load_json(DATA_LAWS); tid = q.get("topic_id", ["gai_speed"])[0]
                for t in data["topics"]:
                    if t["id"] == tid: return self._json({"topic": t})
                return self._json({"error": "topic not found"}, 404)
            if u.path == "/api/search":
                needle = q.get("q", [""])[0].lower().strip()
                hits = []
                data = load_json(DATA_LAWS)
                for t in data["topics"]:
                    for v in t["versions"]:
                        if needle and (needle in (t["title"] + v["text"] + v.get("article","")).lower()):
                            hits.append({"title": t["title"], "article": v.get("article"), "text": v["text"], "source_url": v.get("source_url"), "cbd_url": v.get("cbd_url")})
                try:
                    allf = ROOT / "data" / "all_laws.json"
                    if allf.exists():
                        alld = load_json(allf)
                        for k, a in alld.items():
                            if needle and (needle in (a["title"] + a["text"] + a["article"]).lower()):
                                hits.append({"title": a["title"], "article": a["article"], "text": a["text"][:600], "source_url": a["source_url"], "cbd_url": a["cbd_url"]})
                            if len(hits) >= 40: break
                except Exception as e: log.warning("all search failed %s", e)
                return self._json({"q": needle, "hits": hits[:40]})
            if u.path == "/api/assistant":
                qtext = q.get("q", [""])[0]
                lang_q = q.get("lang", ["ru"])[0]
                needle = qtext.lower().strip()
                if len(needle) < 3: return self._json({"error": "Слишком короткий запрос", "hits": [], "summary": "", "steps": []}, 400)
                words = [w for w in needle.replace(",", " ").split() if len(w) > 3]
                scored = []
                # curated first (higher weight)
                data = load_json(DATA_LAWS)
                for t in data["topics"]:
                    for v in t["versions"]:
                        hay = (t["title"] + " " + v["text"] + " " + v.get("article","")).lower()
                        sc = sum(1 for w in words if w in hay) * 10 + (20 if needle in hay else 0)
                        if sc > 0: scored.append((sc, t["title"], v.get("article"), v["text"][:500], v.get("source_url"), v.get("cbd_url")))
                try:
                    allf = ROOT / "data" / "all_laws.json"
                    if allf.exists():
                        alld = load_json(allf)
                        for k, a in alld.items():
                            hay = (a["title"] + " " + a["text"] + " " + a["article"]).lower()
                            sc = sum(1 for w in words if w in hay) + (10 if needle in hay else 0)
                            if sc > 0: scored.append((sc, a["title"], a["article"], a["text"][:500], a["source_url"], a["cbd_url"]))
                except Exception as e: log.warning("assist all failed %s", e)
                scored = sorted(scored, key=lambda x: x[0], reverse=True)[:5]
                hits = [{"title": s[1], "article": s[2], "text": s[3], "source_url": s[4], "cbd_url": s[5]} for s in scored]
                total = len(scored)
                # category → steps
                low = needle
                if any(k in low for k in ["гаи", "скорость", "пьяный", "опьян", "штраф гаи", "остановил"]): steps = ["Протокол + фото/видео", "Страховка", "Дата правонарушения (важна ст.3 — закон времени деяния)", "Обжалование по закону с доказательствами", "Адвокат до подписания"]
                elif any(k in low for k in ["зарплат", "договор", "уволил", "работ", "айлык"]): steps = ["Переводы зарплаты", "График + переписка", "Зафиксируй в госинспекции", "Сертификат трудового договора", "Адвокат до суда"]
                elif any(k in low for k in ["аренд", "квартира", "займ", "расписк", "долг", "кредит"]): steps = ["Расписка/договор + паспортные данные", "Претензия письменно", "Чеки/переводы", "Свидетели", "Адвокат: письменная форма (ГК 545/725)"]
                elif any(k in low for k in ["мусор", "благоустр", "сосед", "шум"]): steps = ["Фото до/после", "Жалоба в аильный округ", "Протокол", "Свидетели"]
                else: steps = ["Сформулируй clearly: дата, место, факт", "Собери доказательства (фото, переписка)", "Найди статью в Поиске выше", "Адвокат перед подписанием", "Не юридическая консультация"]
                if lang_q == "ky": summary = f"Суроо: {qtext}. Табылды {total} берене. Эң белгилүү — расмий текстти СДБде текшер (КоП 60031 / ГК 57490). Бул кеңеш эмес, машыгуу."
                else: summary = f"По твоей проблеме нашёл {total} релевантных статей из базы 1000+ (КоП 09.10.2026, ГК 28.07.2026). Отвечаю только по официальным текстам со ссылками. Не юридическая консультация — для реального дела нужен адвокат."
                ai_text = ask_claude(qtext, hits)
                if ai_text: summary = ai_text
                return self._json({"q": qtext, "summary": summary, "hits": hits, "steps": steps, "disclaimer": "Не юрконсультация. Проверь в CBD. Ответ на основе поиска, не адвокат.", "ai_model": ai_health().get("model"), "ai_used": bool(ai_text)})
            if u.path == "/api/article":
                aid = q.get("id", [""])[0]; data = load_json(DATA_LAWS)
                for t in data["topics"]:
                    if t["id"] == aid: return self._json({"topic": t})
                return self._json({"error": "article not found"}, 404)
            if u.path == "/api/scenarios":
                data = load_json(DATA_SC)
                return self._json({"scenarios": [{"id": s["id"], "title": s["title"], "year": s["year"], "role": s["role"], "articles": s.get("articles", [])} for s in data["scenarios"]]})
            if u.path == "/api/simulate":
                data = load_json(DATA_SC); sid = q.get("id", ["speed_real"])[0]
                for s in data["scenarios"]:
                    if s["id"] == sid: return self._json({"scenario": s, "disclaimer": data["disclaimer"]})
                return self._json({"error": "scenario not found"}, 404)
            if u.path == "/api/answer":
                data = load_json(DATA_SC); sid = q.get("id", [""])[0]
                step = int(q.get("step", ["0"])[0]); pick = int(q.get("pick", ["0"])[0])
                for s in data["scenarios"]:
                    if s["id"] == sid:
                        if step >= len(s["steps"]): return self._json({"done": True, "checklist": s["checklist"]}, 400)
                        st = s["steps"][step]
                        return self._json({"correct": pick == st["correct"], "why": st["why"], "total": len(s["steps"])})
                return self._json({"error": "scenario not found"}, 404)
            if u.path == "/api/checklist":
                sid = q.get("id", [""])[0]; data = load_json(DATA_SC)
                for s in data["scenarios"]:
                    if s["id"] == sid:
                        txt = ("Чек-лист в суд: " + s['title'] + "\nСтатьи: " + ", ".join(s.get('articles',[])) + "\n" + "\n".join("- " + x for x in s["checklist"]) + "\n\nНе является юридической консультацией. Сверяйся с CBD Минюста.\n")
                        body = txt.encode("utf-8")
                        self.send_response(200); self._headers("text/plain; charset=utf-8", len(body), {"Content-Disposition": f'attachment; filename="checklist_{sid}.txt"'})
                        self.end_headers(); self.wfile.write(body); return
                return self._json({"error": "not found"}, 404)
            return self._json({"error": "not found"}, 404)
        except Exception as e:
            log.exception("error handling %s", self.path)
            return self._json({"error": "internal"}, 500)

if __name__ == "__main__":
    srv = ThreadingHTTPServer((HOST, PORT), H)
    log.info("Serving http://%s:%d/ (sources: KoP 09.10.2026, GK 28.07.2026)", HOST, PORT)
    print(f"KanunTime http://{HOST}:{PORT}/")
    srv.serve_forever()
