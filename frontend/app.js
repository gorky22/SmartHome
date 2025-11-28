// default to '/api/' so when served in dev mode Vite can proxy '/api/*' -> backend
const API_BASE = (window.API_BASE || "").trim() || "/api/";

async function fetchJSON(path) {
  const r = await fetch(API_BASE + path);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

const devicesEl = document.getElementById("devices");
const deviceDetail = document.getElementById("device-detail");
const deviceNameEl = document.getElementById("device-name");
const deviceMeta = document.getElementById("device-meta");
const sensorsEl = document.getElementById("sensors");
const sensorView = document.getElementById("sensor-view");
const sensorTitle = document.getElementById("sensor-title");
const logsTableBody = document.querySelector("#logs-table tbody");
const statCount = document.getElementById("stat-count");
const statAvg = document.getElementById("stat-avg");
const statMin = document.getElementById("stat-min");
const statMax = document.getElementById("stat-max");
const startInput = document.getElementById("start");
const endInput = document.getElementById("end");
const refreshBtn = document.getElementById("refresh-logs");
const backBtn = document.getElementById("back-to-devices");

let currentDevice = null;
let currentSensor = null;
let chart = null;

async function loadDevices() {
  devicesEl.innerHTML = "<li>Loading...</li>";
  try {
    const devices = await fetchJSON("devices");
    devicesEl.innerHTML = "";
    for (const d of devices) {
      const li = document.createElement("li");
      li.innerHTML = `<strong>${
        d.name || d.mac || "device-" + d.id
      }</strong><div style="font-size:12px;color:#9aa7b2">${
        d.location || ""
      } · ${d.last_seen || ""}</div>`;
      li.onclick = () => openDevice(d);
      devicesEl.appendChild(li);
    }
  } catch (e) {
    devicesEl.innerHTML = "<li>Error loading</li>";
    console.error(e);
  }
}

function showDeviceSection() {
  deviceDetail.classList.remove("hidden");
}
function hideDeviceSection() {
  deviceDetail.classList.add("hidden");
}

async function openDevice(device) {
  currentDevice = device;
  currentSensor = null;
  showDeviceSection();
  deviceNameEl.textContent = device.name || device.mac || "device-" + device.id;
  deviceMeta.textContent = `MAC: ${device.mac || "-"} · IP: ${
    device.ip || "-"
  } · Location: ${device.location || "-"} · last seen: ${
    device.last_seen || "-"
  }`;
  sensorsEl.innerHTML = "<li>Loading...</li>";
  sensorView.classList.add("hidden");
  try {
    const sensors = await fetchJSON(`devices/${device.id}/sensors`);
    sensorsEl.innerHTML = "";
    for (const s of sensors) {
      const li = document.createElement("li");
      li.textContent = s.type + (s.unit ? " (" + s.unit + ")" : "");
      li.onclick = () => openSensor(s);
      sensorsEl.appendChild(li);
    }
  } catch (e) {
    sensorsEl.innerHTML = "<li>Error</li>";
    console.error(e);
  }
}

async function openSensor(sensor) {
  currentSensor = sensor;
  sensorView.classList.remove("hidden");
  sensorTitle.textContent =
    sensor.type + (sensor.unit ? " (" + sensor.unit + ")" : "");
  await refreshLogs();
}

function isoLocal(date) {
  if (!date) return "";
  const d = new Date(date);
  return d.toLocaleString();
}

function readStartEnd() {
  const start = startInput.value
    ? new Date(startInput.value).toISOString()
    : undefined;
  const end = endInput.value
    ? new Date(endInput.value).toISOString()
    : undefined;
  return { start, end };
}

async function refreshLogs() {
  if (!currentDevice || !currentSensor) return;
  const { start, end } = readStartEnd();
  const q = new URLSearchParams();
  if (start) q.set("start", start);
  if (end) q.set("end", end);
  try {
    const logs = await fetchJSON(
      `devices/${currentDevice.id}/sensors/${currentSensor.id}/logs?` +
        q.toString()
    );
    const stats = await fetchJSON(
      `devices/${currentDevice.id}/sensors/${currentSensor.id}/stats?` +
        q.toString()
    );

    // populate table
    logsTableBody.innerHTML = "";
    const labels = [];
    const data = [];
    for (const r of logs) {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${isoLocal(r.timestamp)}</td><td>${r.value}</td><td>${
        r.status
      }</td>`;
      logsTableBody.appendChild(tr);
      labels.push(r.timestamp);
      data.push(r.value);
    }

    // stats
    statCount.textContent = stats.count;
    statAvg.textContent = stats.avg ? Number(stats.avg).toFixed(3) : "-";
    statMin.textContent = stats.min ?? "-";
    statMax.textContent = stats.max ?? "-";

    // chart
    const ctx = document.getElementById("chart").getContext("2d");
    if (chart) chart.destroy();
    chart = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels.map((l) => new Date(l).toLocaleString()),
        datasets: [
          {
            label: currentSensor.type,
            data: data,
            borderColor: "#8ab4ff",
            backgroundColor: "rgba(138,180,255,0.12)",
            tension: 0.2,
          },
        ],
      },
      options: { scales: { x: { display: true }, y: { display: true } } },
    });
  } catch (e) {
    console.error("refreshLogs error", e);
  }
}

backBtn.onclick = () => {
  hideDeviceSection();
  currentDevice = null;
  currentSensor = null;
};
refreshBtn.onclick = refreshLogs;

loadDevices();
