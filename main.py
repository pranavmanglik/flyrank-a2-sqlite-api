"""The W2 Task API backed by a persistent SQLite file (Flyrank W3 A2)."""

import os
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

# Keep the default database beside this file, but allow a different path for local checks.
DATABASE_PATH = Path(os.getenv("TASKS_DB_PATH", Path(__file__).with_name("tasks.db")))
app = FastAPI(title="Task API", version="1.0")

SEED_TASKS = [
    ("Read the assignment brief", 0),
    ("Build the API", 0),
    ("Try Swagger UI", 1),
]
CREATE_TASK_BODY = {
    "required": True,
    "content": {
        "application/json": {
            "schema": {
                "type": "object",
                "required": ["title"],
                "properties": {"title": {"type": "string", "minLength": 1}},
            },
            "example": {"title": "Buy milk"},
        }
    },
}
UPDATE_TASK_BODY = {
    "required": True,
    "content": {
        "application/json": {
            "schema": {
                "type": "object",
                "minProperties": 1,
                "properties": {
                    "title": {"type": "string", "minLength": 1},
                    "done": {"type": "boolean"},
                },
            },
            "example": {"done": True},
        }
    },
}


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    # Named columns are easier to read than numeric positions in the route handlers.
    connection.row_factory = sqlite3.Row
    return connection


def as_task(row: sqlite3.Row) -> dict[str, Any]:
    # SQLite stores booleans as 0/1; convert them back to real JSON booleans here.
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


def error(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": message})


async def read_object(request: Request) -> tuple[dict[str, Any] | None, str | None]:
    # Validate the request shape before it reaches any SQL statement.
    try:
        body = await request.json()
    except Exception:
        return None, "Request body must be valid JSON"
    if not isinstance(body, dict):
        return None, "Request body must be a JSON object"
    return body, None


@app.on_event("startup")
def initialize_database() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1))
            )"""
        )
        count = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if count == 0:
            # Seed only an empty table, so a server restart never overwrites saved tasks.
            connection.executemany("INSERT INTO tasks (title, done) VALUES (?, ?)", SEED_TASKS)


@app.get("/", summary="Describe the Task API")
def root() -> dict[str, Any]:
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", summary="Check that the API is running")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tasks", summary="List tasks")
def list_tasks(done: bool | None = None, search: str | None = None) -> list[dict[str, Any]]:
    sql = "SELECT id, title, done FROM tasks"
    clauses: list[str] = []
    values: list[Any] = []
    if done is not None:
        clauses.append("done = ?")
        values.append(int(done))
    if search:
        clauses.append("title LIKE ?")
        # Pass user values separately instead of formatting them into the SQL string.
        values.append(f"%{search}%")
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY id"
    with connect() as connection:
        rows = connection.execute(sql, values).fetchall()
    return [as_task(row) for row in rows]


@app.get("/tasks/{task_id}", summary="Get one task")
def get_task(task_id: int):
    with connect() as connection:
        row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    if row is None:
        return error("Task not found", 404)
    return as_task(row)


@app.post(
    "/tasks",
    status_code=201,
    summary="Create a task",
    openapi_extra={"requestBody": CREATE_TASK_BODY},
)
async def create_task(request: Request):
    body, issue = await read_object(request)
    if issue:
        return error(issue, 400)
    title = body.get("title")
    if not isinstance(title, str) or not title.strip():
        return error("Field 'title' is required and must be a non-empty string", 400)
    with connect() as connection:
        cursor = connection.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)", (title.strip(), 0)
        )
        row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return JSONResponse(status_code=201, content=as_task(row))


@app.put(
    "/tasks/{task_id}",
    summary="Update a task",
    openapi_extra={"requestBody": UPDATE_TASK_BODY},
)
async def update_task(task_id: int, request: Request):
    body, issue = await read_object(request)
    if issue:
        return error(issue, 400)
    if not body or not set(body).intersection({"title", "done"}):
        return error("Provide a non-empty 'title' and/or a boolean 'done'", 400)
    if "title" in body and (not isinstance(body["title"], str) or not body["title"].strip()):
        return error("Field 'title' must be a non-empty string", 400)
    if "done" in body and not isinstance(body["done"], bool):
        return error("Field 'done' must be a boolean", 400)

    with connect() as connection:
        current = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if current is None:
            return error("Task not found", 404)
        title = body.get("title", current["title"])
        done = int(body.get("done", bool(current["done"])))
        connection.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?", (title.strip(), done, task_id)
        )
        updated = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return as_task(updated)


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    with connect() as connection:
        cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount == 0:
            return error("Task not found", 404)
    return Response(status_code=204)


@app.get("/stats", summary="Count tasks")
def stats() -> dict[str, int]:
    with connect() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS total, SUM(done) AS done FROM tasks"
        ).fetchone()
    done_count = row["done"] or 0
    return {"total": row["total"], "done": done_count, "open": row["total"] - done_count}
