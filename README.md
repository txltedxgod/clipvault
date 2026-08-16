# ClipVault

> Self-hosted clipboard history manager with full-text search, snippet tagging, and dark UI.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python)](https://python.org)
[![SQLite](https://img.shields.io/badge/SQLite-Async-003B57?style=flat-square&logo=sqlite)](https://sqlite.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

`#clipboard-manager` `#snippets` `#fastapi` `#sqlite` `#vanilla-js` `#productivity` `#self-hosted`

---

## Features

- **Snippet Management:** Save and organize code snippets with auto-detected languages.
- **Instant Search:** Full-text search across all saved snippet titles and contents.
- **Tag System:** Categorize and filter snippets by multi-tag selection.
- **Dark Theme UI:** Clean, responsive, keyboard-friendly interface with zero external JS dependencies.
- **Dockerized:** Instant self-hosted deployment with Docker and Docker Compose.

## Quick Start

### With Docker

```bash
docker compose up --build
```

### Local Development

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://localhost:8000` in your browser.

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/snippets` | List snippets (query: `q`, `tag`, `limit`, `offset`) |
| `POST` | `/api/snippets` | Create a new snippet |
| `GET` | `/api/snippets/:id` | Get snippet details |
| `PUT` | `/api/snippets/:id` | Update snippet content/tags |
| `DELETE` | `/api/snippets/:id` | Delete snippet |
| `GET` | `/api/tags` | List all unique tags |

## Stack

- **Backend:** FastAPI, SQLAlchemy 2.0 (async), `aiosqlite`
- **Frontend:** Vanilla JavaScript, Modern CSS
- **Container:** Docker & Docker Compose
