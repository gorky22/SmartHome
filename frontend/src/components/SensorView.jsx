import React, { useEffect, useState, useRef } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend
);

// dynamic import / plugin registration for zoom
import zoomPlugin from "chartjs-plugin-zoom";
ChartJS.register(zoomPlugin);

import { useTranslation } from "../i18n.jsx";

export default function SensorView({ device, sensor }) {
  const { t } = useTranslation();
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState({
    count: 0,
    avg: null,
    min: null,
    max: null,
  });
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [loading, setLoading] = useState(false);
  const chartRef = useRef(null);

  // zoom/pan UI state
  const [zoomEnabled, setZoomEnabled] = useState(true);
  const [panEnabled, setPanEnabled] = useState(true);

  useEffect(() => {
    fetchAll();
  }, [device, sensor]);

  async function fetchAll() {
    if (!device || !sensor) return;
    setLoading(true);
    try {
      const q = new URLSearchParams();
      if (start) q.set("start", new Date(start).toISOString());
      if (end) q.set("end", new Date(end).toISOString());
      const logsRes = await fetch(
        `/api/devices/${device.id}/sensors/${sensor.id}/logs?` + q.toString()
      );
      const logsData = await logsRes.json();
      const statsRes = await fetch(
        `/api/devices/${device.id}/sensors/${sensor.id}/stats?` + q.toString()
      );
      const statsData = await statsRes.json();
      setLogs(logsData);
      setStats(statsData);
    } catch (err) {
      console.error(err);
      setLogs([]);
      setStats({ count: 0 });
    }
    setLoading(false);
  }

  const data = {
    labels: logs.map((l) => new Date(l.timestamp).toLocaleString()),
    datasets: [
      {
        label: sensor.type,
        data: logs.map((l) => l.value),
        fill: true,
        tension: 0.28, // smoothing
        borderColor: "#8ab4ff",
        backgroundColor:
          "linear-gradient(180deg, rgba(138,180,255,0.14), rgba(138,180,255,0.02))",
        pointRadius: 3,
        pointHoverRadius: 5,
        borderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        display: true,
        ticks: { maxRotation: 0 },
      },
      y: {
        display: true,
        beginAtZero: false,
      },
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        mode: "index",
        intersect: false,
      },
      zoom: {
        pan: { enabled: panEnabled, mode: "x", modifierKey: "ctrl" },
        zoom: {
          wheel: { enabled: zoomEnabled },
          pinch: { enabled: zoomEnabled },
          mode: "x",
        },
      },
    },
    animation: { duration: 200 },
  };

  return (
    <div className="sensor-view">
      <div className="controls">
        <label>
          {t("from")}{" "}
          <input
            type="datetime-local"
            value={start}
            onChange={(e) => setStart(e.target.value)}
          />
        </label>
        <label>
          {t("to")}{" "}
          <input
            type="datetime-local"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
          />
        </label>
        <button onClick={fetchAll}>{t("refresh")}</button>
      </div>

      <div className="stats">
        <div>
          {t("count")}: {stats.count}
        </div>
        <div>
          {t("avg")}: {stats.avg ? Number(stats.avg).toFixed(3) : "-"}
        </div>
        <div>
          {t("min")}: {stats.min ?? "-"}
        </div>
        <div>
          {t("max")}: {stats.max ?? "-"}
        </div>
      </div>

      {loading ? (
        <div>{t("loading")}</div>
      ) : (
        <>
          <div className="chart-wrap" style={{ height: 320 }}>
            <Line ref={chartRef} data={data} options={options} />
          </div>

          <div className="chart-controls">
            <button onClick={() => setZoomEnabled((v) => !v)} className="btn">
              {zoomEnabled ? `🔍 ${t("zoomOn")}` : `🔍 ${t("zoomOff")}`}
            </button>
            <button onClick={() => setPanEnabled((v) => !v)} className="btn">
              {panEnabled ? `🖐️ ${t("panOn")}` : `🖐️ ${t("panOff")}`}
            </button>
            <button
              onClick={() => {
                const chart =
                  chartRef.current?.chartInstance ??
                  chartRef.current?.instance ??
                  chartRef.current?.getContext?.()?.chart;
                // Chart.js exposes resetZoom method when plugin is active
                try {
                  if (chart && typeof chart.resetZoom === "function")
                    chart.resetZoom();
                  else if (chartRef.current && chartRef.current.resetZoom)
                    chartRef.current.resetZoom();
                } catch (e) {
                  console.warn("resetZoom not available", e);
                }
              }}
              className="btn"
            >
              {t("resetZoom")}
            </button>
          </div>

          <table className="logs-table">
            <thead>
              <tr>
                <th>timestamp</th>
                <th>value</th>
                <th>status</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((r) => (
                <tr key={r.id}>
                  <td>{new Date(r.timestamp).toLocaleString()}</td>
                  <td>{r.value}</td>
                  <td>{r.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
