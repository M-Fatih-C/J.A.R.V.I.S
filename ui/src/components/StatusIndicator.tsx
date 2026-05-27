import { useStore } from "../store";
import type { JarvisStatus } from "../types";

const LABELS: Record<JarvisStatus, string> = {
  idle: "Hazır",
  listening: "Dinliyor",
  thinking: "Düşünüyor",
  speaking: "Yanıtlıyor",
};

export function StatusIndicator() {
  const status = useStore((s) => s.status);
  const connected = useStore((s) => s.connected);

  const cls = connected ? status : "offline";
  const label = connected ? LABELS[status] : "Bağlantı yok";

  return (
    <div className={`status ${cls}`}>
      <span className="dot" />
      <span>J.A.R.V.I.S — {label}</span>
    </div>
  );
}
