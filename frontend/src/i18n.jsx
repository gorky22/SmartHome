import React, {
  createContext,
  useContext,
  useMemo,
  useState,
  useEffect,
} from "react";

const translations = {
  en: {
    title: "SmartHome Dashboard",
    devices: "Devices",
    selectDevice: "Select a device to view sensors and data",
    sensors: "Sensors",
    chooseSensor: "Choose a sensor to see logs & chart",
    from: "From",
    to: "To",
    refresh: "Refresh",
    count: "Count",
    avg: "Avg",
    min: "Min",
    max: "Max",
    loading: "Loading...",
    reload: "Reload",
    back: "Back",
    zoomOn: "Zoom ON",
    zoomOff: "Zoom OFF",
    panOn: "Pan ON (Ctrl)",
    panOff: "Pan OFF",
    resetZoom: "Reset zoom",
  },
  sk: {
    title: "SmartHome Panel",
    devices: "Zariadenia",
    selectDevice: "Vyberte zariadenie pre zobrazenie senzorov a dát",
    sensors: "Senzory",
    chooseSensor: "Vyberte senzor pre zobrazenie záznamov a grafu",
    from: "Od",
    to: "Do",
    refresh: "Obnoviť",
    count: "Počet",
    avg: "Priemer",
    min: "Min",
    max: "Max",
    loading: "Načítavam...",
    reload: "Znovu načítať",
    back: "Späť",
    zoomOn: "Zoom ZAPNUTÝ",
    zoomOff: "Zoom VYPNUTÝ",
    panOn: "PanOVANIE ZAPNUTÉ (Ctrl)",
    panOff: "PanOVANIE VYPNUTÉ",
    resetZoom: "Resetovať zoom",
  },
};

const defaultLang = "en";

const I18nContext = createContext(null);

export function I18nProvider({ children }) {
  const [lang, setLang] = useState(() => {
    try {
      return localStorage.getItem("smarthome.lang") || defaultLang;
    } catch (e) {
      return defaultLang;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem("smarthome.lang", lang);
    } catch (e) {
      // ignore storage errors
    }
  }, [lang]);

  const value = useMemo(
    () => ({
      lang,
      setLang,
      t: (key) => {
        return (
          translations[lang]?.[key] ?? translations[defaultLang][key] ?? key
        );
      },
      available: Object.keys(translations),
    }),
    [lang]
  );

  return React.createElement(I18nContext.Provider, { value }, children);
}

export function useTranslation() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useTranslation must be used inside I18nProvider");
  return ctx;
}

export default { translations };
