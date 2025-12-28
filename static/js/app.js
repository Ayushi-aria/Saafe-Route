// Map Initialization
const map = L.map('map').setView([23.8142, 86.4412], 13); // Center on ISM Dhanbad

// Dark Mode Tile Layer
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 20
}).addTo(map);

let routeLayer = null;
let blockedCoordinates = [];
let isHazardMode = false;

// Markers for key locations
const locations = [
    { name: "ISM Dhanbad (Depot)", lat: 23.8142, lng: 86.4412 },
    { name: "City Centre", lat: 23.8050, lng: 86.4300 },
    { name: "Bank More", lat: 23.7900, lng: 86.4200 },
    { name: "Hirapur", lat: 23.8100, lng: 86.4350 },
    { name: "Station", lat: 23.7957, lng: 86.4266 }
];

locations.forEach(loc => {
    L.circleMarker([loc.lat, loc.lng], {
        radius: 6,
        fillColor: "#818cf8",
        color: "#fff",
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
    }).addTo(map).bindPopup(loc.name);
});

// Fetch and Draw Route
async function fetchRoute() {
    try {
        const response = await fetch('/api/route', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ blocked_coordinates: blockedCoordinates })
        });

        const data = await response.json();

        if (routeLayer) map.removeLayer(routeLayer);

        routeLayer = L.geoJSON(data, {
            style: function (feature) {
                return {
                    color: feature.properties.stroke === 'red' ? '#ef4444' : '#4ade80',
                    weight: 4,
                    opacity: 0.8
                };
            }
        }).addTo(map);

        // Update Metrics
        document.getElementById('total-dist').innerText = `${data.metrics.safe_distance} m`;
        document.getElementById('total-risk').innerText = data.metrics.total_risk;
        document.getElementById('nodes-visited').innerText = data.metrics.nodes_visited;

        document.getElementById('status-text').innerHTML = blockedCoordinates.length > 0
            ? '<span class="status-badge status-blocked">Hazard Avoidance Active</span>'
            : '<span class="status-badge status-safe">Optimal Path</span>';

    } catch (error) {
        console.error("Error fetching route:", error);
    }
}

// Hazard Mode Toggle
const hazardBtn = document.getElementById('hazard-btn');
hazardBtn.addEventListener('click', () => {
    isHazardMode = !isHazardMode;
    hazardBtn.classList.toggle('active');
    hazardBtn.innerText = isHazardMode ? 'Click Map to Block Road' : 'Simulate Hazard';
    map.getContainer().style.cursor = isHazardMode ? 'crosshair' : '';
});

// Map Click Handler
map.on('click', function (e) {
    if (!isHazardMode) return;

    const lat = e.latlng.lat;
    const lng = e.latlng.lng;

    // Add marker for hazard
    L.marker([lat, lng], {
        icon: L.divIcon({
            className: 'custom-div-icon',
            html: "<div style='background-color:#ef4444;width:12px;height:12px;border-radius:50%;border:2px solid white;'></div>",
            iconSize: [12, 12],
            iconAnchor: [6, 6]
        })
    }).addTo(map);

    blockedCoordinates.push([lat, lng]);

    // Refresh Route
    fetchRoute();

    // Turn off hazard mode after one click (optional, but good UX for demo)
    // isHazardMode = false;
    // hazardBtn.classList.remove('active');
    // hazardBtn.innerText = 'Simulate Hazard';
    // map.getContainer().style.cursor = '';
});

// Initial Load
fetchRoute();
