import { create } from "zustand";
import type { ChatMessage, JarvisStatus } from "./types";

interface JarvisState {
  status: JarvisStatus;
  connected: boolean;
  messages: ChatMessage[];
  /** WebSocket adresi (varsayılan: aynı host /ws). */
  wsUrl: string;
  sessionId: string;
  accent: string;

  setStatus: (status: JarvisStatus) => void;
  setConnected: (connected: boolean) => void;
  addMessage: (message: ChatMessage) => void;
  setSettings: (settings: Partial<Pick<JarvisState, "wsUrl" | "sessionId" | "accent">>) => void;
}

function defaultWsUrl(): string {
  if (typeof window === "undefined") return "ws://localhost:8000/ws";
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  // Vite dev sunucusu /ws'i API'ye proxy'ler.
  return `${proto}://${window.location.host}/ws`;
}

export const useStore = create<JarvisState>((set) => ({
  status: "idle",
  connected: false,
  messages: [],
  wsUrl: defaultWsUrl(),
  sessionId: "ui",
  accent: "#38e8ff",

  setStatus: (status) => set({ status }),
  setConnected: (connected) => set({ connected }),
  addMessage: (message) => set((s) => ({ messages: [...s.messages, message] })),
  setSettings: (settings) => set(settings),
}));
