# My task API with SQLite

For this assignment, I took the task API I started in Project 1 and gave it persistent storage. I used Python's built-in `sqlite3` module, so I didn't need to run a separate database server. When I stop and start the API, the tasks stay in `tasks.db` instead of disappearing with the process.

## What I changed

- Kept the task API routes from Project 1
- Created the SQLite database and table when the app starts
- Added three starter tasks only when the database is empty
- Used parameterized SQL values for searches and updates
- Added filtering, search, and task counts using SQL

## How I run it

From this project folder, I create an environment, install the dependencies, and start the API:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

I can try the routes in Swagger at <http://localhost:8000/docs>. By default, the database file is created beside `main.py`. I can set `TASKS_DB_PATH` if I want it somewhere else. The generated `tasks.db` file is ignored by Git.

## Routes

| Method | Path | What I use it for |
| --- | --- | --- |
| GET | `/` | Check the API name and version |
| GET | `/health` | Check that the API and database are available |
| GET | `/tasks` | List tasks, optionally filtering by `done` or `search` |
| GET | `/tasks/{id}` | Get one task |
| POST | `/tasks` | Create a task, for example `{"title":"Write README"}` |
| PUT | `/tasks/{id}` | Update a task's `title`, `done` value, or both |
| DELETE | `/tasks/{id}` | Delete a task |
| GET | `/stats` | Count all, completed, and open tasks |

The API returns JSON error messages for invalid input and missing task IDs. The task data is stored in SQLite using parameterized queries.

## How I check persistence

With the server running, I create a task and list the tasks:

```bash
curl -i -X POST http://localhost:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"SQLite persistence test"}'

curl -i http://localhost:8000/tasks
```

Then I stop the server with `Ctrl+C`, start it again using the Uvicorn command above, and list the tasks once more:

```bash
curl -i http://localhost:8000/tasks
```

I expect to find “SQLite persistence test” after the restart. I also plan to open `tasks.db` in DB Browser for SQLite and inspect the `tasks` table. After I run these checks, I’ll record the actual responses and a query I tried; I haven’t filled in results I haven’t observed yet.

## Test screenshot

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/78c6694e-fb8f-4e6c-bb95-dda1c1c996f8" />

<!-- Add the screenshot here as assets/a2-sqlite-test.png when it is available in this project folder. -->

## What I want to improve next

This project taught me how to keep the API behavior while changing where its data lives. Next, I’m using Postgres and Docker Compose in Project 3 so the API and database can run together in containers.

