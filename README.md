# Plant-Based API (pbapi)

A FastAPI-based backend for the Plant-Based project, providing search and vendor management capabilities.

## Features

- **Search API**: Endpoints for searching plant-based products.
- **Vendor Management**: CRUD operations for vendors (in progress).
- **Health Checks**: Basic and deep health monitoring.
- **Infrastructure**: AWS CDK for deployment.

## Project Structure

- `src/adapters/rest/fastapi_server.py`: FastAPI application definition and local server entry point.
- `src/handlers/`: API route definitions (`search.py`, `health.py`, `vendor.py`).
- `src/schemas/`: Pydantic models for request/response validation.
- `src/adapters/`: Data storage and third-party adapters.
- `appwrite_functions/`: Entry point and configuration for Appwrite deployment.

## Local Development

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)

### Setup

1. Install dependencies:
   ```shell
   uv sync
   ```

2. Run the application:
   ```shell
   uv run uvicorn src.adapters.rest.fastapi_app:app --reload
   ```

The API will be available at `http://127.0.0.1:8000`.
Interactive API documentation (Swagger UI) is available at `http://127.0.0.1:8000/docs`.

## Database Migrations

PostgreSQL migrations use [Alembic](https://alembic.sqlalchemy.org/) for version control, allowing you to upgrade and downgrade database schema versions. A backup is automatically created before each migration.

### Setup Environment Variables
```bash
export DEV_POSTGRES_HOST=localhost
export DEV_POSTGRES_PORT=5432
export DEV_POSTGRES_DB=pbapi_local
export DEV_POSTGRES_USER=postgres
export DEV_POSTGRES_PASSWORD=postgres
```

### Migration Commands
_(make sure PostgreSQL creds are set in the .env file)_

**Run migrations (upgrade to latest):**
```bash
uv run python db_migration.py --env $ENV_NAME --db postgres --action up
```

**Downgrade one revision:**
```bash
uv run python db_migration.py --env dev --db postgres --action down
```

**Downgrade to specific revision:**
```bash
uv run python db_migration.py --env $ENV_NAME --db postgres --action down --revision legacy_000_schema
```

**Show migration history:**
```bash
uv run python db_migration.py --env $ENV_NAME --db postgres --action history
```

**Show current revision:**
```bash
uv run python db_migration.py --env $ENV_NAME --db postgres --action current
```

**Create new migration:**
```bash
uv run python db_migration.py --env $ENV_NAME --db postgres --action create -m "add_new_column"
```

**Skip backup (not recommended for production):**
```bash
uv run python db_migration.py --env $ENV_NAME --db postgres --action up --no-backup
```

### Database Backup Utility

The backup utility creates SQL dumps before migrations and can be used standalone:

```bash
# Create a backup
uv run python db_backup.py backup --env $ENV_NAME

# List available backups
uv run python db_backup.py list --env $ENV_NAME

# Restore from backup
uv run python db_backup.py restore --env $ENV_NAME --file backups/receipt_parser_dev_20260103_120000.sql

# Cleanup old backups (keep last 10)
uv run python db_backup.py cleanup --env $ENV_NAME --keep 10
```

### Migration Options
- `--env`: Required. One of `prod`, `stage`, `dev`, `test`, `local`
- `--db`: Database type. `postgres` (default: `postgres`)
- `--action`: Migration action. One of `up`, `down`, `history`, `current`, `create` (default: `up`)
- `--revision`: Target revision for up/down (default: `head` for up, `-1` for down)
- `--message`, `-m`: Migration message (required for `create` action)
- `--no-backup`: Skip backup before migration

## Testing

Run tests using `pytest`:
```shell
pytest
```

## Deployment

The project uses AWS CDK for deployment. Refer to the `cdk/` directory for infrastructure-related code.
