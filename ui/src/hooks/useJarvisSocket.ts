import { useCallback, useEffect, useRef } from "react";
import { useStore } from "../store";
import type { ServerEvent } from "../types";

const RECONNECT_DELAY_MS = 2000;

/**
 * Jarvis /ws WebSocket'ine bağlanır, gelen event'leri store'a yansıtır ve
 * mesaj göndermek için bir `send` fonksiyonu döndürür. Bağlantı koparsa
 * otomatik yeniden bağlanır.
 */
async function fetchToken(deviceKey: string): Promise<string | null> {
  try {
    const resp = await fetch("/auth/token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ device_key: deviceKey }),
    });
    if (!resp.ok) return null;
    const data = await resp.json();
    return data.access_token as string;
  } catch {
    return null;
  }
}

export function useJarvisSocket(): { send: (message: string) => void } {
  const wsUrl = useStore((s) => s.wsUrl);
  const sessionId = useStore((s) => s.sessionId);
  const deviceKey = useStore((s) => s.deviceKey);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<number | null>(null);

  useEffect(() => {
    const { setConnected, setStatus, addMessage } = useStore.getState();
    let closed = false;

    const connect = async () => {
      // Cihaz anahtarı verilmişse önce token al, WS adresine ?token= ekle.
      let url = wsUrl;
      if (deviceKey) {
        const token = await fetchToken(deviceKey);
        if (token) url = `${wsUrl}?token=${encodeURIComponent(token)}`;
      }
      if (closed) return;
      const ws = new WebSocket(url);
      socketRef.current = ws;

      ws.onopen = () => setConnected(true);

      ws.onmessage = (event) => {
        const data: ServerEvent = JSON.parse(event.data);
        if (data.type === "status" && data.state) {
          setStatus(data.state);
        } else if (data.type === "response") {
          addMessage({
            role: "jarvis",
            content: data.content ?? "",
            lane: data.lane,
            model: data.model,
            latencyMs: data.latency_ms,
          });
          setStatus("speaking");
        } else if (data.type === "error") {
          addMessage({ role: "jarvis", content: `⚠️ ${data.detail ?? "hata"}` });
        }
      };

      ws.onclose = () => {
        setConnected(false);
        setStatus("idle");
        if (!closed) {
          reconnectRef.current = window.setTimeout(connect, RECONNECT_DELAY_MS);
        }
      };

      ws.onerror = () => ws.close();
    };

    void connect();

    return () => {
      closed = true;
      if (reconnectRef.current) window.clearTimeout(reconnectRef.current);
      socketRef.current?.close();
    };
  }, [wsUrl, deviceKey]);

  const send = useCallback(
    (message: string) => {
      const ws = socketRef.current;
      if (!ws || ws.readyState !== WebSocket.OPEN) return;
      useStore.getState().addMessage({ role: "user", content: message });
      ws.send(JSON.stringify({ message, session_id: sessionId }));
    },
    [sessionId],
  );

  return { send };
}
