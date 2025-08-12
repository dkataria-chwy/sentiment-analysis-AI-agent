import React, { useEffect, useRef } from 'react';

type DancingDotsOverlayProps = {
  active: boolean;
  gridSize?: number; // distance between dots in px
  radius?: number;   // base radius in px
  color?: string;    // rgba color
  region?: 'full' | 'centerBand' | 'element';
  elementId?: string; // when region === 'element', restrict to this element's rect
};

/**
 * Animated dots overlay that jitters dots in place with different phases,
 * producing a subtle "random dancing" effect similar to napkin.ai generation.
 * Drawn on a fixed-position canvas above the dotted background and below UI.
 */
export default function DancingDotsOverlay({
  active,
  gridSize = 26,  // reduce dot count for performance
  radius = 1.45,  // a touch larger for a bit more presence
  color = 'rgba(0, 120, 255, 0.5)',
  region = 'centerBand',
  elementId,
}: DancingDotsOverlayProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = Math.min(1.5, Math.max(1, window.devicePixelRatio || 1)); // cap DPR for perf
    const resize = () => {
      const { innerWidth: w, innerHeight: h } = window;
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(document.documentElement);

    let start = performance.now();

    const speed = 6.2;      // even faster animation speed
    const amplitude = 3.9;  // slightly more motion, still smooth

    const draw = (now: number) => {
      const t = (now - start) / 1000; // seconds
      const width = canvas.width / dpr;
      const height = canvas.height / dpr;

      ctx.clearRect(0, 0, width, height);

      // Define drawing bounds based on region
      let xStart = 0;
      let xEnd = width;
      let yStart = 0;
      let yEnd = height;
      if (region === 'centerBand') {
        const bandH = Math.min(320, height * 0.42);
        yStart = (height - bandH) / 2;
        yEnd = (height + bandH) / 2;
      } else if (region === 'element' && elementId) {
        const el = document.getElementById(elementId);
        if (el) {
          const r = el.getBoundingClientRect();
          xStart = Math.max(0, r.left);
          xEnd = Math.min(width, r.right);
          yStart = Math.max(0, r.top);
          yEnd = Math.min(height, r.bottom);
        }
      }

      // We'll cycle colors across a small gradient palette
      const palette = [
        'rgba(59, 130, 246, 0.32)',  // blue-500
        'rgba(99, 102, 241, 0.29)',  // indigo-500
        'rgba(236, 72, 153, 0.28)',  // pink-500
        'rgba(34, 197, 94, 0.26)',   // green-500
        'rgba(234, 179, 8, 0.25)',   // amber-500
      ];
      ctx.globalCompositeOperation = 'source-over';

      // Loop over grid and apply per-dot phase for pseudo-random motion
      for (let y = Math.max(0, Math.floor(yStart / gridSize) * gridSize); y <= yEnd; y += gridSize) {
        for (let x = Math.max(0, Math.floor(xStart / gridSize) * gridSize); x <= xEnd; x += gridSize) {
          // Pseudo-random phase based on coordinates
          const phase = ((x * 0.173 + y * 0.127) % (Math.PI * 2));
          const dx = Math.sin(t * speed + phase) * amplitude;
          const dy = Math.cos(t * speed * 1.21 + phase * 1.37) * amplitude;
          const pulse = 0.85 + 0.35 * Math.sin(t * 1.9 + phase * 2.1);

          const r = radius * pulse;
          const px = x + dx;
          const py = y + dy;
          if (px >= xStart && px <= xEnd && py >= yStart && py <= yEnd) {
            // pick a color from palette based on position
            const ci = Math.abs(Math.floor((x + y) / gridSize) % palette.length);
            ctx.fillStyle = palette[ci];
            ctx.beginPath();
            ctx.arc(px, py, r, 0, Math.PI * 2);
            ctx.fill();
          }
        }
      }

      rafRef.current = requestAnimationFrame(draw);
    };

    let lastRender = 0;
    const tick = (now: number) => {
      // cap to ~30 FPS for stability
      if (now - lastRender > 33) {
        lastRender = now;
        draw(now);
      } else {
        rafRef.current = requestAnimationFrame(tick);
      }
    };

    if (active) rafRef.current = requestAnimationFrame(tick);

    return () => {
      ro.disconnect();
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    };
  }, [active, gridSize, radius, color, region]);

  if (!active) return null;

  return (
    <canvas
      ref={canvasRef}
      style={{ position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 5 }}
    />
  );
}

