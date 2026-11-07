# KanunTime — AI Юридический помощник КР

Чёрная профессиональная платформа: машина времени по закону + симулятор суда + AI чат (Claude Haiku 4.5) пофициальным текстам КоП и ГК КР. RU / KY, без эмодзи.

## Быстрый старт

```bash
cd C:/Users/user/PycharmProjects/law_time_machine
py src/app.py
# open http://127.0.0.1:8765/  (чат отдельный: /chat)
py tests/smoke_test.py
# PASS — ALL REAL PASS
```

## Структура

- `src/app.py` — threaded сервер, API, security-headers, логи
- `src/ai.py` — Claude Haiku 4.5 клиент (fallback на локальный поиск без ключа)
- `static/index.html` — основной сайт (чёрная тема, Space Grotesk + Inter, анимации на скролл)
- `static/chat.html` — отдельный AI чат (/chat)
- `data/laws.json` — 28 curated статей с provenance
- `data/all_laws.json` — 1000+ статей (KoП 574 + ГК 568) для поиска
- `scripts/fetch_all.py` — bulk-краулер с zakon.kg (зеркало CBD)

## API

- `GET /api/laws?year=2026` — статьи по году + time note (КоАП 1998 → КоП 2019)
- `GET /api/search?q=` — поиск по 1000+
- `GET /api/assistant?q=&lang=ru` — AI (Claude Haiku 4.5 при `ANTHROPIC_API_KEY`, иначе fallback)
- `GET /health` — здоровье

## Claude Haiku 4.5

```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY="sk-ant-..."
$env:CLAUDE_MODEL="claude-haiku-4-5-20251001"
py src/app.py
```

Без ключа помощник работает на локальном поиске. Ключ в репозиторий не коммитить (.env в .gitignore).

## Deploy

```bash
# локально
HOST=0.0.0.0 PORT=8765 py src/app.py
# docker
docker compose up --build -d
curl http://localhost:8765/health
```

См. README_DEPLOY.md.

## Данные

Тексты: zakon.kg зеркалит CBD Минюста (КоП 60031, ГК 57490). Сверяй в CBD. Не юрконсультация. До продающей версии нужен юрист (LAWYER_CHECKLIST.md).

## Лицензия

MIT — см. LICENSE.
