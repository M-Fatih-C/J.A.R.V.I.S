import { useEffect } from "react";
import { Scene } from "./components/Scene";
import { StatusIndicator } from "./components/StatusIndicator";
import { ChatPanel } from "./components/ChatPanel";
import { SettingsPanel } from "./components/SettingsPanel";
import { useJarvisSocket } from "./hooks/useJarvisSocket";
import { useStore } from "./store";

export default function App() {
  const { send } = useJarvisSocket();
  const accent = useStore((s) => s.accent);

  useEffect(() => {
    document.documentElement.style.setProperty("--accent", accent);
  }, [accent]);

  return (
    <div className="app">
      <Scene />
      <div className="overlay">
        <StatusIndicator />
        <ChatPanel onSend={send} />
      </div>
      <SettingsPanel />
    </div>
  );
}
