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

export default function SensorView({ device, sensor }) {
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
        borderColor: "#8ab4ff",
        backgroundColor: "rgba(138,180,255,0.08)",
      },
    ],
  };

  return (
    <div className="sensor-view">
      <div className="controls">
        <label>
          From{" "}
          <input
            type="datetime-local"
            value={start}
            onChange={(e) => setStart(e.target.value)}
          />
        </label>
        <label>
          To{" "}
          <input
            type="datetime-local"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
          />
        </label>
        <button onClick={fetchAll}>Refresh</button>
      </div>

      <div className="stats">
        <div>Count: {stats.count}</div>
        <div>Avg: {stats.avg ? Number(stats.avg).toFixed(3) : "-"}</div>
        <div>Min: {stats.min ?? "-"}</div>
        <div>Max: {stats.max ?? "-"}</div>
      </div>

      {loading ? (
        <div>Loading...</div>
      ) : (
        <>
          <div style={{ height: 240 }}>
            <Line data={data} />
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
