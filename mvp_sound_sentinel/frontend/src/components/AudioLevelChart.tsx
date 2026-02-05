import { useEffect, useRef, useState } from 'react';

interface Props {
  currentLevel?: number;
}

export function AudioLevelChart({ currentLevel = 0 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioLevelsRef = useRef<{ timestamp: number; level: number }[]>([]);
  const animationRef = useRef<number>();
  const [tooltip, setTooltip] = useState<{ x: number; y: number; level: number } | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const padding = { top: 10, right: 10, bottom: 20, left: 30 };
    const width = canvas.width / dpr - padding.left - padding.right;
    const height = canvas.height / dpr - padding.top - padding.bottom;
    const timeWindow = 10000; // 5 секунд

    const handleMouseMove = (event: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const x = event.clientX - rect.left - padding.left;
      const now = Date.now();
      const startTime = now - timeWindow;

      if (audioLevelsRef.current.length === 0) return;

      const closestPoint = audioLevelsRef.current.reduce((prev, curr) => {
        const prevX = ((prev.timestamp - startTime) / timeWindow) * width;
        const currX = ((curr.timestamp - startTime) / timeWindow) * width;
        return Math.abs(currX - x) < Math.abs(prevX - x) ? curr : prev;
      });

      const pointX = padding.left + ((closestPoint.timestamp - startTime) / timeWindow) * width;
      const pointY = padding.top + (height - (closestPoint.level / 100) * height);
      setTooltip({ x: pointX, y: pointY, level: closestPoint.level });
    };

    const handleMouseLeave = () => setTooltip(null);

    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseleave', handleMouseLeave);

    const draw = () => {
      const now = Date.now();
      if (currentLevel > 0) {
        audioLevelsRef.current.push({ timestamp: now, level: currentLevel });
      }
      audioLevelsRef.current = audioLevelsRef.current.filter(p => now - p.timestamp < timeWindow);

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#FFFFFF';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      ctx.save();
      ctx.translate(padding.left, padding.top);

      // Draw grid and labels
      ctx.strokeStyle = '#f0f0f0';
      ctx.lineWidth = 1;
      ctx.font = '10px sans-serif';
      ctx.fillStyle = '#9ca3af';

      // Y-axis
      for (let i = 0; i <= 4; i++) {
        const y = (height / 4) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
        ctx.fillText(`${100 - i * 25}`, -padding.left + 5, y + 3);
      }

      // X-axis
      for (let i = 0; i <= 5; i++) {
        const x = (width / 5) * i;
        ctx.fillText(`-${5 - i}s`, x - 5, height + 15);
      }

      // Draw chart
      if (audioLevelsRef.current.length > 1) {
        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 2;
        ctx.beginPath();
        const startTime = now - timeWindow;
        audioLevelsRef.current.forEach((point, index) => {
          const x = ((point.timestamp - startTime) / timeWindow) * width;
          const y = height - (point.level / 100) * height;
          if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        });
        ctx.stroke();

        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.2)');
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0)');
        ctx.fillStyle = gradient;
        ctx.beginPath();
        const firstPoint = audioLevelsRef.current[0];
        ctx.moveTo(((firstPoint.timestamp - startTime) / timeWindow) * width, height);
        audioLevelsRef.current.forEach(point => {
          const x = ((point.timestamp - startTime) / timeWindow) * width;
          const y = height - (point.level / 100) * height;
          ctx.lineTo(x, y);
        });
        const lastPoint = audioLevelsRef.current[audioLevelsRef.current.length - 1];
        ctx.lineTo(((lastPoint.timestamp - startTime) / timeWindow) * width, height);
        ctx.closePath();
        ctx.fill();
      }
      ctx.restore();

      // Draw tooltip
      if (tooltip) {
        ctx.strokeStyle = '#9ca3af';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(tooltip.x, padding.top);
        ctx.lineTo(tooltip.x, height + padding.top);
        ctx.stroke();

        ctx.fillStyle = '#3b82f6';
        ctx.beginPath();
        ctx.arc(tooltip.x, tooltip.y, 4, 0, 2 * Math.PI);
        ctx.fill();
      }

      animationRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, [currentLevel, tooltip]);

  return (
    <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-4 sm:p-6 shadow-xl border border-gray-100">
      <h3 className="text-lg sm:text-xl font-bold mb-4 bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">Уровень звука</h3>
      <div className="relative h-48">
        <canvas
          ref={canvasRef}
          className="absolute top-0 left-0 w-full h-full rounded-lg"
        />
        {tooltip && (
          <div 
            className="absolute bg-gray-800 text-white text-xs rounded py-1 px-2 pointer-events-none"
            style={{ left: tooltip.x + 5, top: tooltip.y - 30, transform: 'translateX(-50%)' }}
          >
            {tooltip.level.toFixed(1)} dB
          </div>
        )}
      </div>
    </div>
  );
}
