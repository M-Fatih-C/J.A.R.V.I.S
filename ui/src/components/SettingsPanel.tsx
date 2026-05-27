import { useState } from "react";
import { useStore } from "../store";

export function SettingsPanel() {
  const [open, setOpen] = useState(false);
  const { wsUrl, sessionId, accent, setSettings } = useStore();

  return (
    <>
      <button
        className="settings-toggle"
        onClick={() => setOpen((o) => !o)}
        title="Ayarlar"
      >
        ⚙
      </button>
      {open && (
        <div className="settings">
          <h3>Ayarlar</h3>
          <label>
            WebSocket adresi
            <input
              value={wsUrl}
              onChange={(e) => setSettings({ wsUrl: e.target.value })}
            />
          </label>
          <label>
            Oturum kimliği
            <input
              value={sessionId}
              onChange={(e) => setSettings({ sessionId: e.target.value })}
            />
          </label>
          <label>
            Vurgu rengi
            <input
              type="color"
              value={accent}
              onChange={(e) => setSettings({ accent: e.target.value })}
            />
          </label>
        </div>
      )}
    </>
  );
}
