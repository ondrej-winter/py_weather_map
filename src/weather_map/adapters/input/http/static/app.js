const map = L.map('map').setView([50.0755, 14.4378], 6);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors',
}).addTo(map);

let heatLayer = L.heatLayer([], { radius: 28, blur: 20, maxZoom: 8 }).addTo(map);
let availableLayers = [];

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
  const heatPoints = payload.points.map((point) => [point.latitude, point.longitude, point.intensity]);
  heatLayer.setLatLngs(heatPoints);
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