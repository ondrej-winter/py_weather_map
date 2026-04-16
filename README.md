# weather_map

Local Python web application for exploring historical weather data from Open-Meteo on top of an OpenStreetMap map.

## Features

- Interactive OpenStreetMap map rendered with Leaflet
- Historical weather heatmaps for temperature, precipitation, humidity, and wind speed
- Snapshot mode for a single UTC day/hour
- Range mode for simple date-range aggregations
- On-demand historical fetches from Open-Meteo with an in-memory cache seam for future persistence

## Setup

Install dependencies with `uv`:

```bash
uv sync --group dev
```

## Run locally

Start the local web app:

```bash
uv run weather-map
```

Then open `http://127.0.0.1:8000` in your browser.

## Configuration

Environment variables:

- `WEATHER_MAP_OPENMETEO_BASE_URL` (default: `https://archive-api.open-meteo.com/v1/archive`)
- `WEATHER_MAP_REQUEST_TIMEOUT_SECONDS` (default: `15.0`)
- `WEATHER_MAP_HOST` (default: `127.0.0.1`)
- `WEATHER_MAP_PORT` (default: `8000`)
- `WEATHER_MAP_DEFAULT_GRID_ROWS` (default: `8`)
- `WEATHER_MAP_DEFAULT_GRID_COLUMNS` (default: `8`)
- `WEATHER_MAP_MAX_GRID_ROWS` (default: `20`)
- `WEATHER_MAP_MAX_GRID_COLUMNS` (default: `20`)

Snapshot mode uses a single UTC date plus hour. Range mode aggregates data across the selected date interval.

## Quality checks

Run the local checks:

```bash
uv run ruff format .
uv run ruff check .
uv run mypy .
uv run pytest
```

## Architecture overview

- `src/weather_map/domain/` contains pure domain logic, weather-layer metadata, and aggregation services.
- `src/weather_map/application/` contains use cases, ports, and DTOs.
- `src/weather_map/adapters/input/http/` contains the FastAPI app and static browser UI.
- `src/weather_map/adapters/output/` contains the Open-Meteo client and in-memory cache.
- `tests/` mirrors the source layout for unit and integration tests.