# Inventory Management API

A backend API for small businesses to manage products and stock movements, built as a real-world portfolio project — not a tutorial exercise. It solves an actual inventory problem for a single-owner hair salon: guaranteeing stock never goes negative, keeping a permanent audit trail of every change, and flagging products that need restocking.

**Live API docs:** https://inventory-management-3yz5.onrender.com/docs

---

## Table of contents

- [The problem](#the-problem)
- [Tech stack](#tech-stack)
- [Architecture](#architecture)
- [Key design decisions](#key-design-decisions)
- [Getting started](#getting-started)
- [Running with Docker](#running-with-docker)
- [Running the test suite](#running-the-test-suite)
- [Deployment](#deployment)
- [Known limitations / next steps](#known-limitations--next-steps)
- [License](#license)

---

## The problem

Only one person (the salon owner) uses this system — but a single user can still trigger two nearly-simultaneous requests against the same product: two sales rung up back-to-back on a slow connection, a double-tap on a touchscreen, a network retry. If two stock-out requests for the same product aren't handled correctly, stock can end up wrong — or negative — silently, with no error to signal it. On top of that, a small business needs a permanent, auditable history of what happened to its stock and why, not just a running total that could have been quietly edited. The system needs to:

- Guarantee a product's stock never goes negative, even when two requests for the same product arrive at nearly the same instant
- Keep a permanent, append-only history of every stock change — created, never edited or deleted
- Distinguish cleanly between a product simply not existing and there not being enough stock to fulfill a request
- Flag products at or below a configurable low-stock threshold
- Report the total value of everything currently in stock

---

## Tech stack

- **Python 3.13** / **FastAPI**
- **PostgreSQL** (Supabase) with **SQLAlchemy 2.0**, fully async
- **Alembic** — database migrations
- **Pydantic v2** — request/response validation
- **JWT** authentication (access + refresh tokens)
- **pytest** — 28 automated tests, including a real concurrency test using `asyncio.gather`
- **Docker** — containerized deployment
- Deployed on **Render**, database on **Supabase**

---

## Architecture

```
inventory-management/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── deps.py
│   │   ├── security.py
│   │   └── exceptions.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user_model.py
│   │   ├── category_model.py
│   │   ├── product_model.py
│   │   └── stock_movement_model.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth_schema.py
│   │   ├── common_schema.py
│   │   ├── user_schema.py
│   │   ├── category_schema.py
│   │   ├── product_schema.py
│   │   └── stock_movement_schema.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── category_service.py
│   │   ├── product_service.py
│   │   └── stock_movement_service.py
│   └── routers/
│       ├── __init__.py
│       ├── auth_router.py
│       ├── category_router.py
│       ├── product_router.py
│       ├── stock_movement_router.py
│       └── reports_router.py
│
├── alembic/
│   ├── versions/
│   │   ├── 8e5bed2a75f7_create_initial_tables.py
│   │   └── a50d2df2c3e2_add_timezone_to_datetime_columns.py
│   ├── env.py
│   ├── README
│   └── script.py.mako
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth_router.py
│   ├── test_category_router.py
│   ├── test_product_router.py
│   ├── test_stock_movement_router.py
│   └── test_reports_router.py
│
├── create_user.py
├── .dockerignore
├── .env.example
├── .gitattributes
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── pytest.ini
├── README.md
└── requirements.txt
```

The business logic in `services/` is kept separate from the HTTP layer in `routers/`, so the stock and pricing rules can be tested directly without going through the API, and so the router layer stays focused on translating between HTTP and domain exceptions. Each service file is a set of plain async functions taking an `AsyncSession` directly, rather than a class — there's no shared state complex enough to justify one.

---

## Key design decisions

- **Atomic stock updates, no distributed lock needed.** Stock movements update `Product.current_stock` through a single conditional `UPDATE ... WHERE current_stock >= quantity` statement, computed entirely in SQL. A stock change is simple arithmetic on one row, so the database's own row-level locking is enough to guarantee correctness under concurrent requests — no Redis or external lock required. Verified with a dedicated test that fires two simultaneous stock-out requests against the same product and confirms exactly one succeeds.
- **Domain exceptions, not raw database errors.** Business rule violations (insufficient stock, duplicate SKU or category name, missing resource) are raised as typed exceptions and translated into clean HTTP responses by a single table of exception handlers.
- **Append-only movement history.** `StockMovement` records are never updated or deleted. Corrections are made via new, compensating entries, preserving a full audit trail.
- **`DB_URL` stays local for day-to-day development.** `.env` defaults to a local PostgreSQL instance; the production `DB_URL` is only swapped in temporarily, to run a migration or create the production user, then reverted — so local experimentation never touches real business data.
- **Authentication required everywhere** except `/auth/login` and `/auth/refresh` — appropriate for a single-user system handling real business data.
- **Test isolation via SAVEPOINT rollback.** Each test runs inside its own savepoint on a shared connection, rolled back at teardown, so tests never leak data into each other, no matter how many commits the code under test performs.
- **No rate limiting, pagination on categories, or token revocation yet** — deliberate scope decisions for a single-user system at this stage. See [Known limitations](#known-limitations--next-steps).

---

## Getting started

### Prerequisites

- Python 3.13+
- A PostgreSQL database (this project uses [Supabase](https://supabase.com) in production)

### Local setup

```bash
git clone https://github.com/bertollimb/inventory-management.git
cd inventory-management
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in the required values:

```
DB_URL=postgresql+asyncpg://...
JWT_SECRET=
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
PROJECT_NAME=Inventory Management API
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

Apply migrations and run the server:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000/docs` (Swagger UI).

### Authentication

There's no public sign-up endpoint, since the system is single-user by design — the salon owner is the only account expected to exist. The account is created once via `create_user.py`, which reads `INITIAL_USER_EMAIL`, `INITIAL_USER_FULL_NAME`, and `INITIAL_USER_PASSWORD` from `.env` rather than containing any credentials itself, so it's safe to commit. It refuses to run if a user already exists.

```bash
python create_user.py
```

1. Log in via `POST /auth/login` (OAuth2 password flow — email/password as form data) to receive an access token and a refresh token
2. Send the access token on protected endpoints:
```
   Authorization: Bearer <access_token>
```
3. Use `POST /auth/refresh` with the refresh token to obtain a new access token once the current one expires (the refresh token itself is not rotated)

---

## Running with Docker

```bash
docker compose up --build
```

The container reads the same `.env` file as local development, via `env_file`. If `DB_URL` points to `localhost` (the default for day-to-day local development), swap it for `host.docker.internal` before running Docker locally — a container can't reach `localhost` on the host machine directly. In production, `DB_URL` points to the managed Supabase instance instead, so this only matters for local Docker testing.

---

## Running the test suite

Requires a separate local PostgreSQL database for tests (set `TEST_DB_URL` in `.env` — this database is never touched by the main application):

```bash
pytest -v
```

28 tests covering:
- **Auth**: login success/failure (including the same response for a wrong password and an unknown email, to avoid leaking which emails exist), refresh token issuance and validation
- **Categories / Products**: full CRUD, auth enforcement, duplicate name/SKU rejection, missing-category validation
- **Stock Movements**: entry/exit stock updates, insufficient-stock rejection, `created_by` sourced from the authenticated user rather than the request body, filtering by product, and a concurrency test firing two simultaneous stock-out requests against the same product to confirm exactly one succeeds
- **Reports**: low-stock threshold, total stock value calculation

---

## Deployment

- **API**: Docker container on [Render](https://render.com) (Frankfurt region), built directly from the repository's `Dockerfile`
- **Database**: [Supabase](https://supabase.com) — managed PostgreSQL (Frankfurt region), accessed through the Session pooler for IPv4 compatibility with a persistent backend
- **Frontend**: React, planned for [Vercel](https://vercel.com) — not yet built

Both services run in the same region to minimize latency between them. Environment variables are configured directly on Render and are never baked into the Docker image — `.dockerignore` explicitly excludes `.env`, `venv/`, and other files that shouldn't ship inside the container.

---

## Known limitations / next steps

- **Password recovery** — resetting the account password currently requires a manual database edit; no self-service or script-based flow yet
- **Token revocation** — refresh tokens are stateless and not rotated on use, so a leaked refresh token can't be invalidated before it expires
- **No pagination on categories** — `GET /categories` returns the full list; fine at the current data volume, unlike `/products` and `/movements`, which are already paginated
- **No DELETE endpoints** — categories and products can't be deleted via the API yet (the database's `RESTRICT` foreign keys already prevent deleting one that's in use, but there's no path for retiring one that isn't)
- **`is_active` on User has no real effect in a single-user system** — deactivating the only account would lock out the only person who can use it; the field made more sense when multiple users were still a possibility
- **No login rate limiting** — acceptable without a cache/lock layer in the current stack, but would need Redis (or similar) added if abuse ever became a concern

---

## License

See [`LICENSE`](./LICENSE).