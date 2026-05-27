import { Canvas } from "@react-three/fiber";
import { Sparkles, Stars } from "@react-three/drei";
import { useStore } from "../store";
import { JarvisCore } from "./JarvisCore";
import { VoiceWave } from "./VoiceWave";

/** Tam ekran holografik 3B sahne (çekirdek + dalga + parçacıklar). */
export function Scene() {
  const accent = useStore((s) => s.accent);
  return (
    <Canvas className="scene" camera={{ position: [0, 0, 6], fov: 50 }}>
      <color attach="background" args={["#04070d"]} />
      <fog attach="fog" args={["#04070d", 6, 15]} />
      <ambientLight intensity={0.3} />
      <pointLight position={[4, 4, 4]} intensity={1.2} color={accent} />
      <pointLight position={[-4, -2, -4]} intensity={0.6} color={accent} />
      <JarvisCore />
      <VoiceWave />
      <Sparkles count={120} scale={10} size={2} speed={0.3} color={accent} />
      <Stars radius={40} depth={30} count={1500} factor={3} fade speed={1} />
    </Canvas>
  );
}
