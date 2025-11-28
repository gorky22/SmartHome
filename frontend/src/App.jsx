import React, { useEffect, useState } from "react";
import DeviceList from "./components/DeviceList";
import SensorView from "./components/SensorView";

export default function App() {
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [selectedSensor, setSelectedSensor] = useState(null);
  // mobile toggle for the sidebar (device list)
  const [showSidebar, setShowSidebar] = useState(false);

  useEffect(() => {
    // nothing special now
  }, []);

  return (
    <div className="container">
      <header>
        <div className="header-row">
          <button
            className="mobile-toggle"
            onClick={() => setShowSidebar((s) => !s)}
            aria-label="Toggle devices list"
          >
            ☰
          </button>
          <h1>SmartHome Dashboard</h1>
        </div>
      </header>
      <main>
        <aside className={`sidebar ${showSidebar ? "open" : "closed"}`}>
          <DeviceList
            onSelect={(device) => {
              setSelectedDevice(device);
              setSelectedSensor(null);
              // close sidebar on small screens after choosing a device
              setShowSidebar(false);
            }}
            selected={selectedDevice}
          />
        </aside>
        <section className="content">
          {!selectedDevice ? (
            <div className="hero">Select a device to view sensors and data</div>
          ) : (
            <div>
              <div className="device-meta">
                <h2>{selectedDevice.name || selectedDevice.mac}</h2>
                <div className="meta">
                  {selectedDevice.location || "no location"} •{" "}
                  {selectedDevice.ip || "-"}
                </div>
              </div>
              <div className="area">
                <div className="left">
                  <h3>Sensors</h3>
                  <ul className="sensors-list">
                    {/* load sensors using SensorList inside DeviceList — simpler: fetch sensors on select */}
                    <DeviceSensors
                      device={selectedDevice}
                      onSelect={(s) => {
                        setSelectedSensor(s);
                        // close the device list to focus on sensor view on mobile
                        setShowSidebar(false);
                      }}
                      selectedSensor={selectedSensor}
                    />
                  </ul>
                </div>
                <div className="right">
                  {!selectedSensor ? (
                    <div className="placeholder">
                      Choose a sensor to see logs & chart
                    </div>
                  ) : (
                    <SensorView
                      device={selectedDevice}
                      sensor={selectedSensor}
                    />
                  )}
                </div>
              </div>
            </div>
          )}
        </section>
      </main>
      <footer>Simple SmartHome demo — React + Vite</footer>
    </div>
  );
}

function DeviceSensors({ device, onSelect, selectedSensor }) {
  const [sensors, setSensors] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!device) return;
    setLoading(true);
    fetch(`/api/devices/${device.id}/sensors`)
      .then((r) => r.json())
      .then((d) => setSensors(d))
      .catch((e) => {
        console.error(e);
        setSensors([]);
      })
      .finally(() => setLoading(false));
  }, [device]);

  if (loading) return <div>Loading sensors...</div>;
  return (
    <>
      {sensors.map((s) => (
        <li
          key={s.id}
          className={selectedSensor?.id === s.id ? "selected" : ""}
          onClick={() => onSelect(s)}
        >
          {s.type} {s.unit ? `(${s.unit})` : ""}
        </li>
      ))}
    </>
  );
}
