# AI Study Planner

AI Study Planner is a Flask-based study planning application that helps students organize tasks, track progress, and generate a daily study schedule. It uses server-rendered Jinja templates, SQLite persistence, and a layered backend structure for clean routing, business logic, and data access.

## Features

- User registration, login, logout, and protected dashboard access
- Task creation, filtering, deletion, and status updates
- Status-aware dashboard metrics for to-do, in-progress, and completed work
- Upcoming deadlines panel that excludes completed tasks
- Daily schedule generation from current tasks
- Analytics views for category distribution and weekly progress
- JSON endpoints for dashboard fragments and task operations
- Deployment files for Gunicorn, Docker, Nginx, Render, and Railway

## Tech Stack

| Layer | Tools |
| --- | --- |
| Backend | Python, Flask, Jinja2 |
| Database | SQLite |
| Auth/Security | Flask sessions, bcrypt, itsdangerous |
| Testing | pytest |
| Deployment | Gunicorn, Docker, Docker Compose, Nginx |

## Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── routes/
│   │   ├── services/
│   │   └── utils/
│   ├── config/
│   ├── instance/
│   ├── scripts/
│   ├── tests/
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── static/
│   └── templates/
├── deployment/
│   ├── nginx/
│   ├── scripts/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── gunicorn.conf.py
│   ├── railway.toml
│   └── render.yaml
├── docs/
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11 or newer
- `pip`
- `venv`

Docker is optional and only required for containerized deployment.

### Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
python backend/scripts/init_db.py
python backend/run.py
```

Open the app at:

```text
http://localhost:5000
```

### Environment Variables

The app reads environment variables from `backend/.env`.

| Variable | Purpose | Default |
| --- | --- | --- |
| `SECRET_KEY` | Flask session and token signing key | Required for production |
| `DATABASE_PATH` | SQLite database path relative to `backend/` unless absolute | `instance/study.db` |
| `FLASK_DEBUG` | Enables Flask debug mode with `1` | `0` |
| `SESSION_COOKIE_SECURE` | Sends cookies only over HTTPS when enabled | `0` |
| `HOST` | Development server host | `0.0.0.0` |
| `PORT` | Application port | `5000` |
| `WEB_CONCURRENCY` | Gunicorn worker count | `2` |
| `GUNICORN_THREADS` | Gunicorn thread count per worker | `2` |
| `GUNICORN_TIMEOUT` | Gunicorn request timeout in seconds | `120` |
| `LOG_LEVEL` | Gunicorn log level | `info` |

## Testing

Run the backend test suite:

```bash
pytest backend/tests -q
```

Current verified result:

```text
42 passed
```

## Deployment

### Gunicorn

```bash
python -m gunicorn -c deployment/gunicorn.conf.py backend.run:app
```

### Startup Script

```bash
bash deployment/scripts/start_backend.sh
```

The startup script initializes the database and starts the app with Gunicorn. If `PORT` is not set, it automatically chooses an available port starting at `5000`.

### Docker

```bash
docker build -f deployment/Dockerfile -t ai-study-planner .
docker run --env-file backend/.env -p 5000:5000 ai-study-planner
```

### Docker Compose With Nginx

```bash
docker compose -f deployment/docker-compose.yml up --build
```

Default local endpoints:

- Flask app: `http://localhost:5000`
- Nginx proxy: `http://localhost:8080`

## Routes

### Web Pages

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/` | Dashboard |
| `GET`, `POST` | `/register` | Register a user |
| `GET`, `POST` | `/login` | Log in |
| `GET`, `POST` | `/logout` | Log out |
| `GET` | `/schedule` | Generated study schedule |
| `GET` | `/analytics` | Analytics dashboard |

### Task Endpoints

| Method | Route | Description |
| --- | --- | --- |
| `POST` | `/add` | Create a task from the dashboard |
| `POST` | `/api/tasks` | Create a task via JSON or form data |
| `GET`, `POST` | `/delete/<id>` | Delete a task from the dashboard |
| `DELETE` | `/api/tasks/<id>` | Delete a task via API |
| `POST` | `/task/<id>/status` | Update task status from the dashboard |
| `PUT` | `/api/tasks/<id>/status` | Update task status via API |
| `GET` | `/api/dashboard-fragments` | Refresh dashboard partial HTML |

## Architecture

- Routes handle HTTP requests, sessions, redirects, and JSON responses.
- Services validate inputs and coordinate task, schedule, and analytics workflows.
- Repositories isolate SQLite queries from the rest of the application.
- Templates render the dashboard, task cards, sidebar, schedule, analytics, and auth pages.

## Useful Commands

```bash
# Run locally with Flask
python backend/run.py

# Run on a different port
PORT=5001 python backend/run.py

# Recreate the SQLite database
python backend/scripts/init_db.py

# Run all tests
pytest backend/tests -q
```
