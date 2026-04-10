/**
 * ShaderBackground.jsx
 * Fixed WebGL mesh gradient behind the entire app.
 * Uses @paper-design/shaders-react MeshGradient.
 * Very dark zinc/amber palette — subtle, not distracting.
 */
import { MeshGradient } from "@paper-design/shaders-react";
import { useEffect, useState } from "react";

export default function ShaderBackground() {
  const [dimensions, setDimensions] = useState({ width: 1920, height: 1080 });

  useEffect(() => {
    const update = () =>
      setDimensions({ width: window.innerWidth, height: window.innerHeight });
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  return (
    <div className="fixed inset-0 -z-10 pointer-events-none">
      <MeshGradient
        width={dimensions.width}
        height={dimensions.height}
        speed={0.15}
        distortion={0.4}
        colors={[
          "#09090b",   // zinc-950
          "#0c0a00",   // near black with amber tint
          "#1a0f00",   // very dark amber
          "#09090b",   // zinc-950
          "#110900",   // warmest dark
          "#0d0d0d",   // neutral dark
        ]}
      />
    </div>
  );
}
