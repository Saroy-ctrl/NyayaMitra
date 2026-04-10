import { useRef, useEffect } from "react";

function NoiseCanvas({ patternRefreshInterval = 3, patternAlpha = 18 }) {
  const ref = useRef(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    let frame = 0;
    let animId = 0;
    const S = 1024;

    const resize = () => {
      canvas.width = S;
      canvas.height = S;
      canvas.style.width = "100vw";
      canvas.style.height = "100vh";
    };

    const drawGrain = () => {
      const img = ctx.createImageData(S, S);
      const d = img.data;
      for (let i = 0; i < d.length; i += 4) {
        const v = Math.random() * 255;
        d[i] = v; d[i + 1] = v; d[i + 2] = v; d[i + 3] = patternAlpha;
      }
      ctx.putImageData(img, 0, 0);
    };

    const loop = () => {
      if (frame % patternRefreshInterval === 0) drawGrain();
      frame++;
      animId = requestAnimationFrame(loop);
    };

    window.addEventListener("resize", resize);
    resize();
    loop();

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(animId);
    };
  }, [patternRefreshInterval, patternAlpha]);

  return (
    <canvas
      ref={ref}
      className="pointer-events-none absolute inset-0"
      style={{ imageRendering: "pixelated" }}
    />
  );
}

export default function AppBackground() {
  return (
    <div className="fixed inset-0 -z-10 bg-zinc-950">
      {/* Amber radial spotlight — top-center, bleeds into mid-page */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_90%_55%_at_50%_0%,rgba(251,146,60,0.18),transparent_70%)]" />
      {/* Secondary warm glow — lower center */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_40%_at_50%_100%,rgba(251,146,60,0.07),transparent_70%)]" />
      {/* Dot grid — full coverage, no mask, lower opacity for subtlety */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage: "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.07) 1px, transparent 0)",
          backgroundSize: "22px 22px",
        }}
      />
      {/* Bottom vignette */}
      <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-transparent to-transparent pointer-events-none" />
      {/* Animated film grain */}
      <NoiseCanvas patternRefreshInterval={3} patternAlpha={16} />
    </div>
  );
}
