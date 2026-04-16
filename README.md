# weather_map

Python application scaffold for a weather map project using a hexagonal architecture.

## Setup

Install dependencies with `uv`:

```bash
uv sync --group dev
```

## Quality checks

Run the local checks:

```bash
uv run ruff format .
uv run ruff check .
uv run mypy .
uv run pytest
```

## Architecture overview

- `src/weather_map/domain/` contains pure domain logic and business rules.
- `src/weather_map/application/` contains use cases, ports, and DTOs.
- `src/weather_map/adapters/` contains input and output adapters.
- `tests/` mirrors the source layout for unit and integration tests.