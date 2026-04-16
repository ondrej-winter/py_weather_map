const map = L.map('map').setView([50.0755, 14.4378], 6);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors',
}).addTo(map);

let availableLayers = [];

function createTriangulatedSurfaceLayer() {
  return L.Layer.extend({
    initialize() {
      this._payload = null;
    },

    onAdd(targetMap) {
      this._map = targetMap;
      this._canvas = L.DomUtil.create('canvas', 'leaflet-layer');
      this._canvas.style.pointerEvents = 'none';
      const pane = targetMap.getPanes().overlayPane;
      pane.appendChild(this._canvas);
      targetMap.on('move zoom resize', this._reset, this);
      this._reset();
    },

    onRemove(targetMap) {
      targetMap.off('move zoom resize', this._reset, this);
      if (this._canvas) {
        L.DomUtil.remove(this._canvas);
      }
    },

    setPayload(payload) {
      this._payload = payload;
      this._redraw();
    },

    _reset() {
      if (!this._map || !this._canvas) {
        return;
      }
      const size = this._map.getSize();
      const topLeft = this._map.containerPointToLayerPoint([0, 0]);
      L.DomUtil.setPosition(this._canvas, topLeft);
      this._canvas.width = size.x;
      this._canvas.height = size.y;
      this._redraw();
    },

    _redraw() {
      if (!this._map || !this._canvas) {
        return;
      }
      const context = this._canvas.getContext('2d');
      context.clearRect(0, 0, this._canvas.width, this._canvas.height);
      if (!this._payload || !this._payload.points.length) {
        return;
      }

      const grid = new Map();
      this._payload.points.forEach((point) => {
        grid.set(`${point.row_index}:${point.column_index}`, point);
      });

      for (let row = 0; row < this._payload.grid_spec.rows - 1; row += 1) {
        for (let column = 0; column < this._payload.grid_spec.columns - 1; column += 1) {
          const topLeft = grid.get(`${row}:${column}`);
          const topRight = grid.get(`${row}:${column + 1}`);
          const bottomLeft = grid.get(`${row + 1}:${column}`);
          const bottomRight = grid.get(`${row + 1}:${column + 1}`);
          if (!topLeft || !topRight || !bottomLeft || !bottomRight) {
            continue;
          }
          this._drawTriangle(context, topLeft, topRight, bottomLeft);
          this._drawTriangle(context, bottomRight, topRight, bottomLeft);
        }
      }

      this._drawSampleMarkers(context, this._payload.points);
    },

    _drawTriangle(context, first, second, third) {
      const a = this._map.latLngToContainerPoint([first.latitude, first.longitude]);
      const b = this._map.latLngToContainerPoint([second.latitude, second.longitude]);
      const c = this._map.latLngToContainerPoint([third.latitude, third.longitude]);
      const intensity = (first.intensity + second.intensity + third.intensity) / 3;
      context.beginPath();
      context.moveTo(a.x, a.y);
      context.lineTo(b.x, b.y);
      context.lineTo(c.x, c.y);
      context.closePath();
      context.fillStyle = colorForIntensity(intensity);
      context.globalAlpha = 0.72;
      context.fill();
      context.globalAlpha = 1;
    },

    _drawSampleMarkers(context, points) {
      context.fillStyle = 'rgba(255, 255, 255, 0.85)';
      points.forEach((point) => {
        const projected = this._map.latLngToContainerPoint([point.latitude, point.longitude]);
        context.beginPath();
        context.arc(projected.x, projected.y, 2, 0, Math.PI * 2);
        context.fill();
      });
    },
  });
}

function colorForIntensity(intensity) {
  const hue = 240 - (240 * Math.max(0, Math.min(1, intensity)));
  return `hsla(${hue}, 85%, 50%, 1)`;
}

const TriangulatedSurfaceLayer = createTriangulatedSurfaceLayer();
const surfaceLayer = new TriangulatedSurfaceLayer().addTo(map);

const form = document.getElementById('controls-form');
const layerSelect = document.getElementById('layer-select');
const aggregationSelect = document.getElementById('aggregation-select');
const modeSelect = document.getElementById('mode-select');
const startDateInput = document.getElementById('start-date');
const endDateInput = document.getElementById('end-date');
const snapshotHourInput = document.getElementById('snapshot-hour');
const statusEl = document.getElementById('status');

function setDefaultDates() {
  const today = new Date();
  const end = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate() - 1));
  const start = new Date(end);
  start.setUTCDate(start.getUTCDate() - 6);
  startDateInput.value = start.toISOString().slice(0, 10);
  endDateInput.value = end.toISOString().slice(0, 10);
}

function updateAggregationOptions() {
  const selectedLayer = availableLayers.find((option) => option.layer === layerSelect.value);
  aggregationSelect.innerHTML = '';
  if (!selectedLayer) {
    return;
  }
  selectedLayer.supported_range_aggregations.forEach((aggregation) => {
    const option = document.createElement('option');
    option.value = aggregation;
    option.textContent = aggregation;
    if (aggregation === selectedLayer.default_range_aggregation) {
      option.selected = true;
    }
    aggregationSelect.appendChild(option);
  });
}

function updateModeControls() {
  const isSnapshot = modeSelect.value === 'snapshot';
  snapshotHourInput.disabled = !isSnapshot;
  endDateInput.disabled = isSnapshot;
  aggregationSelect.disabled = isSnapshot;
  if (isSnapshot) {
    endDateInput.value = startDateInput.value;
  }
}

async function loadLayers() {
  const response = await fetch('/api/layers');
  availableLayers = await response.json();
  layerSelect.innerHTML = '';
  availableLayers.forEach((option) => {
    const item = document.createElement('option');
    item.value = option.layer;
    item.textContent = `${option.label} (${option.unit})`;
    layerSelect.appendChild(item);
  });
  updateAggregationOptions();
}

function buildQueryString() {
  const bounds = map.getBounds();
  const params = new URLSearchParams({
    north: bounds.getNorth().toString(),
    south: bounds.getSouth().toString(),
    east: bounds.getEast().toString(),
    west: bounds.getWest().toString(),
    layer: layerSelect.value,
    mode: modeSelect.value,
    start_date: startDateInput.value,
    grid_rows: document.getElementById('grid-rows').value,
    grid_columns: document.getElementById('grid-columns').value,
  });
  if (modeSelect.value === 'snapshot') {
    params.set('end_date', startDateInput.value);
    params.set('snapshot_hour', snapshotHourInput.value);
  } else {
    params.set('end_date', endDateInput.value);
    params.set('aggregation', aggregationSelect.value);
  }
  return params.toString();
}

async function refreshHeatmap() {
  statusEl.textContent = 'Loading heatmap…';
  const response = await fetch(`/api/heatmap?${buildQueryString()}`);
  const payload = await response.json();
  if (!response.ok) {
    statusEl.textContent = payload.detail || 'Failed to load heatmap';
    return;
  }
  surfaceLayer.setPayload(payload);
  statusEl.textContent = `Loaded ${payload.sample_count} samples for ${payload.layer} (${payload.unit})${payload.from_cache ? ' from cache' : ''}.`;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  await refreshHeatmap();
});

layerSelect.addEventListener('change', () => {
  updateAggregationOptions();
});

modeSelect.addEventListener('change', () => {
  updateModeControls();
});

map.on('moveend', () => {
  refreshHeatmap().catch((error) => {
    statusEl.textContent = error.message;
  });
});

setDefaultDates();
updateModeControls();

loadLayers()
  .then(() => refreshHeatmap())
  .catch((error) => {
    statusEl.textContent = error.message;
  });
