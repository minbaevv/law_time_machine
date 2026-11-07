#!/usr/bin/env python3
"""Claude Haiku 4.5 client for assistant. Falls back to local retrieval if no key.
Model: claude-haiku-4-5-20251001 (override via CLAUDE_MODEL)
Env: ANTHROPIC_API_KEY required for live calls. Never log keys.
"""
import json, os, sys, urllib.request
from pathlib import Path

MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
API = "https://api.anthropic.com/v1/messages"

SYSTEM = """Ты помощник KanunTime для Кыргызстана. Отвечаешь только на основе приведённых статей (КоП 09.10.2026, ГК 28.07.2026). Ссылайся на номера статей и источники. Не даёшь финальных юридических решений. Всегда: это не юрконсультация, проверь в CBD Минюста (cbd.minjust.gov.kg), для реального дела — адвокат. Ответ на языке пользователя (RU/KY). Коротко, по делу, шаги. Без эмодзи."""

def ask_claude(question: str, hits):
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key:
        return None  # fallback
    ctx = "\n\n".join([f"[{h.get('article','')}] {h.get('title','')}\n{h.get('text','')[:700]}\nИсточник: {h.get('source_url','')}" for h in hits[:5]])
    user = f"Вопрос пользователя: {question}\n\nСтатьи:\n{ctx}\n\nОтветь по-русски или кыргызски (как вопрос), дай шаги и дисклеймер."
    payload = {"model": MODEL, "max_tokens": 1200, "system": SYSTEM, "messages": [{"role": "user", "content": user}]}
    try:
        req = urllib.request.Request(API, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01", "User-Agent": "KanunTime/1.0"})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read().decode("utf-8", "ignore"))
        text = "".join([b.get("text","") for b in data.get("content",[]) if b.get("type") == "text"])
        return text.strip() or None
    except Exception as e:
        print(f"[ai] claude failed: {e}", file=sys.stderr)
        return None

def health():
    return {"model": MODEL, "configured": bool(os.getenv("ANTHROPIC_API_KEY", "").strip())}
