# ADR 0001: Use a lightweight FastAPI + Leaflet UI for v1 weather-map visualization

## Status

Accepted

## Context

The repository currently starts from a minimal Python hexagonal scaffold. The first functional release needs to visualize historical weather data from Open-Meteo on top of OpenStreetMap in a local interactive application, while staying aligned with the current Python-first structure and avoiding unnecessary frontend complexity.

## Decision

For v1, the application will use:

- FastAPI as the local HTTP adapter and JSON API surface
- Uvicorn as the local ASGI server
- `httpx` for Open-Meteo archive API access
- A server-served HTML/CSS/JavaScript UI with Leaflet and OpenStreetMap tiles
- A heatmap overlay rendered in the browser using `leaflet.heat`
- An in-memory cache behind an application port so persistent storage can be added later

The application core remains hexagonal: domain and application layers own weather analysis, aggregation, and response shaping; Open-Meteo, HTTP, and browser concerns remain in adapters.

## Consequences

### Positive

- Delivers a working local interactive map quickly from the current scaffold
- Preserves hexagonal boundaries and keeps the core independent of frameworks
- Avoids a separate SPA toolchain and Node-based build system for the first release
- Leaves a clean seam for introducing persistent storage later

### Negative

- Frontend assets depend on CDN-hosted Leaflet libraries in v1
- The initial UI is intentionally simple and not optimized for large-scale client-side state management
- In-memory caching is process-local and not durable