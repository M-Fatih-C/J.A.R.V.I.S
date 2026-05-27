import { useCallback, useEffect, useRef } from "react";
import { useStore } from "../store";
import type { ServerEvent } from "../types";

const RECONNECT_DELAY_MS = 2000;

/**
 * Jarvis /ws WebSocket'ine bağlanır, gelen event'leri store'a yansıtır ve
 * mesaj göndermek için bir `send` fonksiyonu döndürür. Bağlantı koparsa
 * otomatik yeniden bağlanır.
 */
export function useJarvisSocket(): { send: (message: string) => void } {
  const wsUrl = useStore((s) => s.wsUrl);
  const sessionId = useStore((s) => s.sessionId);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<number | null>(null);

  useEffect(() => {
    const { setConnected, setStatus, addMessage } = useStore.getState();
    let closed = false;

    const connect = () => {
      const ws = new WebSocket(wsUrl);
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

    connect();

    return () => {
      closed = true;
      if (reconnectRef.current) window.clearTimeout(reconnectRef.current);
      socketRef.current?.close();
    };
  }, [wsUrl]);

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
