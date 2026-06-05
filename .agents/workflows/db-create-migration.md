# Create Database Migration

Generate a new Alembic migration from model changes.

* Ask the user for a migration description if not provided
* Run `uv run alembic revision --autogenerate -m "<description>"`
* Report the generated migration file path
