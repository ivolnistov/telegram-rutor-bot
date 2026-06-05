# Full Dev Environment

Start the complete local development environment: infrastructure, backend API, and frontend.

* First, start infrastructure: `docker compose -f docker-compose-dev.yml up -d postgres redis qbittorrent`
* Wait for all containers to be healthy: `docker compose -f docker-compose-dev.yml ps`
* Then start the backend API in the background: `uv run uvicorn src.telegram_rutor_bot.web.app:app --reload --port 8088 --host 0.0.0.0`
* Then start the frontend dev server in the background: `cd frontend && npm run dev`
* Report all running services and their URLs:
  - API: http://localhost:8088
  - Frontend: http://localhost:5174
  - Postgres: localhost:5433
  - Redis: localhost:6380
  - qBittorrent: http://localhost:8090
