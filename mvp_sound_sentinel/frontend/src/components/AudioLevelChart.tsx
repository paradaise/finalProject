import { useEffect, useRef, useState } from 'react';

interface Props {
  currentLevel?: number;
}

export function AudioLevelChart({ currentLevel = 0 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioLevelsRef = useRef<{ timestamp: number; level: number }[]>([]);
  const animationRef = useRef<number>();
  const [tooltip, setTooltip] = useState<{ x: number; y: number; level: number } | null>(null);

  // Sound Intensity Progress Bar
  const intensity = Math.min(100, Math.max(0, currentLevel));
  const intensityColor = intensity > 80 ? 'bg-red-500' : intensity > 50 ? 'bg-orange-500' : intensity > 25 ? 'bg-yellow-500' : 'bg-green-500';

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

    const padding = { top: 10, right: 10, bottom: 10, left: 10 };
    const width = canvas.width / dpr - padding.left - padding.right;
    const height = canvas.height / dpr - padding.top - padding.bottom;
    const timeWindow = 5000; // 5 seconds window as requested previously

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
      ctx.fillStyle = '#f8fafc'; // Matches the light grey background in screenshot
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      ctx.save();
      ctx.translate(padding.left, padding.top);

      // Draw chart
      if (audioLevelsRef.current.length > 1) {
        ctx.strokeStyle = '#3b82f6'; // Blue line
        ctx.lineWidth = 2;
        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';
        ctx.beginPath();
        const startTime = now - timeWindow;
        audioLevelsRef.current.forEach((point, index) => {
          const x = ((point.timestamp - startTime) / timeWindow) * width;
          const y = height - (point.level / 100) * height;
          if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        });
        ctx.stroke();
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
    <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col gap-6">
      {/* Sound Intensity Section */}
      <div className="flex flex-col gap-2">
        <div className="flex justify-between items-center">
          <span className="text-gray-600 font-medium">Sound Intensity</span>
          <span className="text-gray-900 font-bold">{currentLevel.toFixed(0)} dB</span>
        </div>
        <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-green-400 via-yellow-400 to-red-500 transition-all duration-300"
            style={{ width: `${intensity}%` }}
          />
        </div>
      </div>

      {/* Live Audio Waveform Section */}
      <div className="flex flex-col gap-3">
        <span className="text-gray-600 font-medium">Live Audio Waveform</span>
        <div className="relative h-40 bg-slate-50 rounded-2xl overflow-hidden">
          <canvas
            ref={canvasRef}
            className="absolute top-0 left-0 w-full h-full cursor-crosshair"
          />
          {tooltip && (
            <div 
              className="absolute bg-white/90 backdrop-blur-sm border border-gray-200 shadow-xl rounded-lg py-1.5 px-3 pointer-events-none transition-all duration-75 flex items-center gap-2"
              style={{ left: tooltip.x, top: tooltip.y - 45, transform: 'translateX(-50%)' }}
            >
              <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
              <span className="text-gray-900 font-bold text-sm whitespace-nowrap">{tooltip.level.toFixed(1)} dB</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
