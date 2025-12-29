import React, { useEffect, useState } from "react";

import { useTranslation } from "../i18n.jsx";

export default function DeviceList({ onSelect, selected }) {
  const { t } = useTranslation();
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    load();
  }, []);

  async function load() {
    setLoading(true);
    try {
      const res = await fetch("/api/devices");
      if (!res.ok) throw new Error("failed");
      const data = await res.json();
      setDevices(data);
    } catch (err) {
      console.error(err);
      setDevices([]);
    }
    setLoading(false);
  }

  return (
    <div>
      <div className="list-header">
        <span>{t("devices")}</span>
        <button onClick={load} title="Reload">
          ⟳
        </button>
      </div>
      {loading && <div>{t("loading")}</div>}
      <ul className="device-list">
        {devices.map((d) => (
          <li
            key={d.id}
            className={selected?.id === d.id ? "active" : ""}
            onClick={() => onSelect(d)}
          >
            <div className="title">{d.name || d.mac || "device-" + d.id}</div>
            <div className="sub">
              {d.location || ""} · {d.last_seen || ""}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
