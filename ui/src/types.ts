export type JarvisStatus = "idle" | "thinking" | "speaking" | "listening";

export interface ChatMessage {
  role: "user" | "jarvis";
  content: string;
  lane?: string;
  model?: string;
  latencyMs?: number;
}

/** Sunucudan (/ws) gelen event'ler. */
export interface ServerEvent {
  type: "status" | "response" | "error";
  state?: JarvisStatus;
  content?: string;
  lane?: string;
  model?: string;
  latency_ms?: number;
  detail?: string;
}
