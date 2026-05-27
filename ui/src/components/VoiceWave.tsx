import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import type { Group, Mesh } from "three";
import { useStore } from "../store";
import type { JarvisStatus } from "../types";

const COUNT = 48;
const RADIUS = 2.1;

const AMPLITUDE: Record<JarvisStatus, number> = {
  idle: 0.2,
  listening: 0.7,
  thinking: 1.0,
  speaking: 1.5,
};

/** Çekirdeğin çevresinde duruma göre dalgalanan ses çubukları halkası. */
export function VoiceWave() {
  const status = useStore((s) => s.status);
  const accent = useStore((s) => s.accent);
  const groupRef = useRef<Group>(null);
  const bars = useRef<(Mesh | null)[]>([]);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    const amp = AMPLITUDE[status];
    for (let i = 0; i < COUNT; i++) {
      const bar = bars.current[i];
      if (!bar) continue;
      bar.scale.y = 0.15 + Math.abs(Math.sin(t * 3 + i * 0.4)) * amp;
    }
    if (groupRef.current) groupRef.current.rotation.y = t * 0.1;
  });

  return (
    <group ref={groupRef}>
      {Array.from({ length: COUNT }, (_, i) => {
        const angle = (i / COUNT) * Math.PI * 2;
        return (
          <mesh
            key={i}
            ref={(el) => {
              bars.current[i] = el;
            }}
            position={[Math.cos(angle) * RADIUS, 0, Math.sin(angle) * RADIUS]}
            rotation={[0, -angle, 0]}
          >
            <boxGeometry args={[0.05, 1, 0.05]} />
            <meshStandardMaterial
              color={accent}
              emissive={accent}
              emissiveIntensity={0.6}
            />
          </mesh>
        );
      })}
    </group>
  );
}
