# KanunTime — Deploy (turnkey)

Location: `C:/Users/user/PycharmProjects/law_time_machine/`

## Local
```
cd C:/Users/user/PycharmProjects/law_time_machine
py src/app.py
# http://127.0.0.1:8765/  health: /health
py tests/smoke_test.py
```

## Production env
```
HOST=0.0.0.0
PORT=8765
py src/app.py
curl http://127.0.0.1:8765/health
```

## Docker
```
docker compose up --build -d
docker compose ps
curl http://localhost:8765/health
docker compose logs -f web
docker compose down
```

## Reverse proxy
Point nginx/Caddy to :8765. TLS at proxy. App already sets security headers.

## Product notes
- Theme: black professional (#07090F), no emojis. UI RU/KY with persistence.
- Data: KoP 09.10.2026 (60031), GK 28.07.2026. Texts via zakon.kg mirror, links to CBD. Not legal advice.
- Before commercial sale: add auth/billing, lawyer sign-off per article, expand beyond 9 articles via parser.

## Files
- src/app.py (ThreadingHTTPServer, env HOST/PORT, security headers, logging)
- static/index.html (dark UI, RU/KY, scroll nav, animations)
- data/laws.json (9 real articles with provenance), data/scenarios.json (5 linked)
- Dockerfile, docker-compose.yml, .env.example, requirements.txt (stdlib, no deps)
