import { useEffect, useRef, useState } from "react";
import { useStore } from "../store";

interface ChatPanelProps {
  onSend: (message: string) => void;
}

export function ChatPanel({ onSend }: ChatPanelProps) {
  const messages = useStore((s) => s.messages);
  const connected = useStore((s) => s.connected);
  const status = useStore((s) => s.status);
  const [text, setText] = useState("");
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || !connected) return;
    onSend(trimmed);
    setText("");
  };

  return (
    <div className="chat">
      <div className="messages" ref={listRef}>
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.content}
            {m.role === "jarvis" && m.lane && (
              <span className="meta">
                {m.lane} · {m.model}
                {m.latencyMs ? ` · ${Math.round(m.latencyMs)}ms` : ""}
              </span>
            )}
          </div>
        ))}
      </div>
      <form onSubmit={submit}>
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={connected ? "Bir şey sorun, efendim…" : "Bağlanılıyor…"}
          disabled={!connected}
        />
        <button type="submit" disabled={!connected || status === "thinking"}>
          Gönder
        </button>
      </form>
    </div>
  );
}
