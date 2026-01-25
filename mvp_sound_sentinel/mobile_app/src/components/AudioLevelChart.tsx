import { useEffect, useRef } from 'react';

interface Props {
  deviceId: string;
  currentLevel?: number;
}

export function AudioLevelChart({ deviceId, currentLevel = 0 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioLevelsRef = useRef<number[]>([]);
  const animationRef = useRef<number>();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Устанавливаем размер canvas
    canvas.width = canvas.offsetWidth * 2;
    canvas.height = canvas.offsetHeight * 2;
    ctx.scale(2, 2);

    const width = canvas.offsetWidth;
    const height = canvas.offsetHeight;

    // Максимальное количество точек для отображения
    const maxPoints = 60;

    const draw = () => {
      // Добавляем текущий уровень
      audioLevelsRef.current.push(currentLevel);
      if (audioLevelsRef.current.length > maxPoints) {
        audioLevelsRef.current.shift();
      }

      // Очищаем canvas
      ctx.clearRect(0, 0, width, height);

      // Рисуем фон
      ctx.fillStyle = '#f3f4f6';
      ctx.fillRect(0, 0, width, height);

      // Рисуем сетку
      ctx.strokeStyle = '#e5e7eb';
      ctx.lineWidth = 1;
      
      // Горизонтальные линии
      for (let i = 0; i <= 4; i++) {
        const y = (height / 4) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // Рисуем график уровня звука
      if (audioLevelsRef.current.length > 1) {
        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 2;
        ctx.beginPath();

        audioLevelsRef.current.forEach((level, index) => {
          const x = (index / maxPoints) * width;
          const y = height - (level / 100) * height; // Нормализуем 0-100 к высоте canvas

          if (index === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        });

        ctx.stroke();

        // Заполняем область под графиком
        ctx.fillStyle = 'rgba(59, 130, 246, 0.1)';
        ctx.beginPath();
        ctx.moveTo(0, height);
        
        audioLevelsRef.current.forEach((level, index) => {
          const x = (index / maxPoints) * width;
          const y = height - (level / 100) * height;
          ctx.lineTo(x, y);
        });
        
        ctx.lineTo(width, height);
        ctx.closePath();
        ctx.fill();
      }

      // Рисуем текущий уровень
      if (currentLevel > 0) {
        ctx.fillStyle = '#3b82f6';
        ctx.font = '12px sans-serif';
        ctx.fillText(`${currentLevel.toFixed(1)} dB`, 5, 15);
      }

      animationRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [currentLevel]);

  return (
    <div className="bg-white rounded-xl p-4 shadow-sm">
      <h3 className="text-sm font-medium text-gray-700 mb-2">Уровень звука (dB)</h3>
      <canvas
        ref={canvasRef}
        className="w-full h-32 rounded"
        style={{ width: '100%', height: '128px' }}
      />
    </div>
  );
}
