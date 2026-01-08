import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';
import { useState, useEffect } from 'react';

export function SoundIntensityGraph() {
  const [data, setData] = useState(() => {
    const initialData = [];
    for (let i = 0; i < 20; i++) {
      initialData.push({
        time: i,
        intensity: Math.floor(Math.random() * 40) + 30,
      });
    }
    return initialData;
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setData(prev => {
        const newData = [...prev.slice(1)];
        newData.push({
          time: prev[prev.length - 1].time + 1,
          intensity: Math.floor(Math.random() * 40) + 30,
        });
        return newData;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="mt-4">
      <p className="text-gray-700 text-sm mb-2">Live Audio Waveform</p>
      <div className="bg-gray-50 rounded-xl p-4">
        <ResponsiveContainer width="100%" height={120}>
          <LineChart data={data}>
            <XAxis 
              dataKey="time" 
              hide 
            />
            <YAxis 
              hide 
              domain={[0, 100]} 
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'rgba(0, 0, 0, 0.8)', 
                border: 'none', 
                borderRadius: '8px',
                fontSize: '12px',
                color: '#fff'
              }}
              formatter={(value: number) => [`${value} dB`, 'Intensity']}
              labelFormatter={() => 'Live'}
            />
            <Line 
              type="monotone" 
              dataKey="intensity" 
              stroke="#3b82f6" 
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
