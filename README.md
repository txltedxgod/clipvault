# ClipVault

Self-hosted clipboard history manager. Save snippets, search them, tag and organize.

## Features

- Save and organize code snippets
- Full-text search across all snippets
- Tag system with filtering
- Syntax highlighting support (language labels)
- Dark theme UI
- Docker ready

## Quick Start

```bash
# with docker
docker compose up --build

# or manually
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000 in your browser.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/snippets | List snippets (query: q, tag) |
| POST | /api/snippets | Create snippet |
| GET | /api/snippets/:id | Get snippet by id |
| PUT | /api/snippets/:id | Update snippet |
| DELETE | /api/snippets/:id | Delete snippet |
| GET | /api/tags | List all tags |

## Stack

- FastAPI + SQLAlchemy 2.0 (async)
- SQLite (aiosqlite)
- Vanilla JS frontend
- Docker

## TODO

- [ ] keyboard shortcuts for quick save
- [ ] export/import snippets
- [ ] syntax highlighting in editor
