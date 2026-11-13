# W3 A2 — Connect the CRUD API to SQLite

This standalone version keeps the A1 routes and stores tasks in `tasks.db` using Python's built-in `sqlite3`. It creates the database/table on startup, inserts three examples only when the table is empty, and uses bound `?` parameters for SQL values. Filtering, search, and task counts are also performed in SQL.

## Run

From this folder with Python 3.10 or newer:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open <http://localhost:8000/docs>. The database is created beside `main.py`; set `TASKS_DB_PATH` to choose another location. `tasks.db` is ignored by Git so a clean checkout creates its own seed data.

## Endpoints

The same routes as A1: `GET /`, `GET /health`, `GET /tasks`, `GET /tasks/{id}`, `POST /tasks`, `PUT /tasks/{id}`, `DELETE /tasks/{id}`, and the optional `GET /stats`. Error bodies use `{"error":"..."}`. Search and filters use parameterized SQLite queries.

## Persistence checkpoint

```bash
curl -i http://localhost:8000/tasks
curl -i -X POST http://localhost:8000/tasks -H 'Content-Type: application/json' -d '{"title":"Survives restart"}'
# Stop and restart uvicorn, then list tasks again:
curl -i http://localhost:8000/tasks
```

Open `tasks.db` with DB Browser for SQLite and capture a screenshot for your submission. Paste a real SQL query and its observed result into this README after you run it. The A1 endpoint checks should work unchanged: that is evidence the API contract survived a storage change.

## Assignment steps

Suggested commits: create SQLite database; database read endpoints; insert; update/delete; explore SQL in DB Browser; document and publish. The optional AI rematch must stay in its own folder or branch and needs your own comparison. A public GitHub repo, the DB Browser screenshot, real curl output, and honest commit history remain submission steps.
