import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { MeshDistortMaterial } from "@react-three/drei";
import type { Mesh } from "three";
import { useStore } from "../store";
import type { JarvisStatus } from "../types";

interface CoreParams {
  distort: number;
  speed: number;
  scale: number;
}

const PARAMS: Record<JarvisStatus, CoreParams> = {
  idle: { distort: 0.25, speed: 1.2, scale: 1.0 },
  listening: { distort: 0.4, speed: 2.0, scale: 1.05 },
  thinking: { distort: 0.65, speed: 4.0, scale: 1.08 },
  speaking: { distort: 0.5, speed: 3.0, scale: 1.14 },
};

/** Duruma göre nabız atan, bozulan holografik Jarvis çekirdeği. */
export function JarvisCore() {
  const status = useStore((s) => s.status);
  const accent = useStore((s) => s.accent);
  const meshRef = useRef<Mesh>(null);
  // drei MeshDistortMaterial örneğinin tip imzası dışa aktarılmadığından any.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const matRef = useRef<any>(null);

  useFrame((_, dt) => {
    const target = PARAMS[status];
    const k = Math.min(1, dt * 3);
    if (meshRef.current) {
      meshRef.current.rotation.y += dt * 0.15;
      meshRef.current.rotation.x += dt * 0.05;
      const cur = meshRef.current.scale.x;
      meshRef.current.scale.setScalar(cur + (target.scale - cur) * k);
    }
    if (matRef.current) {
      matRef.current.distort += (target.distort - matRef.current.distort) * k;
      matRef.current.speed = target.speed;
    }
  });

  return (
    <mesh ref={meshRef}>
      <icosahedronGeometry args={[1, 16]} />
      <MeshDistortMaterial
        ref={matRef}
        color={accent}
        emissive={accent}
        emissiveIntensity={0.45}
        roughness={0.15}
        metalness={0.6}
        distort={0.25}
        speed={1.2}
      />
    </mesh>
  );
}
