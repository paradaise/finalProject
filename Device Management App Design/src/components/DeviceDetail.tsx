import { useState, useEffect } from 'react';
import { Volume2, Activity, Wifi, Thermometer, Cpu, Clock } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { apiClient } from '../api/client';

interface DeviceDetailProps {
  deviceId: string;
  onBack: () => void;
}

interface AudioEvent {
  id: string;
  sound_type: string;
  confidence: number;
  timestamp: string;
  db_level: number;
  intensity: number;
  description: string;
}

interface DeviceStats {
  temperature: number;
  cpu_load: number;
  wifi_ssid: string;
}

interface RealtimeData {
  sound_type: string;
  db_level: number;
  audio_waveform: number[];
  device_stats: DeviceStats;
}

export function DeviceDetail({ deviceId, onBack }: DeviceDetailProps) {
  const [currentSound, setCurrentSound] = useState<string>('No sound detected');
  const [currentDb, setCurrentDb] = useState<number>(0);
  const [waveform, setWaveform] = useState<number[]>([]);
  const [events, setEvents] = useState<AudioEvent[]>([]);
  const [deviceStats, setDeviceStats] = useState<DeviceStats | null>(null);
  const [chartData, setChartData] = useState<any[]>([]);

  useEffect(() => {
    // Загрузка истории событий
    const loadEvents = async () => {
      try {
        const eventsData = await apiClient.getDeviceEvents(deviceId);
        setEvents(eventsData);
        
        // Подготовка данных для графика
        const chart = eventsData.slice(-20).map(event => ({
          time: new Date(event.timestamp).toLocaleTimeString(),
          db: event.db_level || 0
        }));
        setChartData(chart);
      } catch (error) {
        console.error('Error loading events:', error);
      }
    };

    loadEvents();

    // WebSocket для реального времени
    const ws = apiClient.connectWebSocket();
    
    ws.onmessage = (event) => {
      try {
        const data: RealtimeData = JSON.parse(event.data);
        
        if (data.device_stats) {
          setDeviceStats(data.device_stats);
        }
        
        setCurrentSound(data.sound_type || 'No sound detected');
        setCurrentDb(data.db_level || 0);
        setWaveform(data.audio_waveform || []);
        
        // Обновление графика в реальном времени
        setChartData(prev => {
          const newData = [...prev, {
            time: new Date().toLocaleTimeString(),
            db: data.db_level || 0
          }];
          return newData.slice(-20); // Последние 20 точек
        });
      } catch (error) {
        console.error('WebSocket error:', error);
      }
    };

    return () => {
      ws.close();
    };
  }, [deviceId]);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <button 
          onClick={onBack}
          className="mb-4 text-blue-600 hover:text-blue-800 font-medium"
        >
          ← Back to devices
        </button>
        <h1 className="text-3xl font-bold text-gray-900">Device Details</h1>
      </div>

      {/* Current Recognition */}
      <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Volume2 className="w-5 h-5 text-blue-600" />
          Current Recognition
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <p className="text-sm text-gray-500 mb-1">Sound Detected</p>
            <p className="text-2xl font-bold text-gray-900">{currentSound}</p>
          </div>
          
          <div>
            <p className="text-sm text-gray-500 mb-1">Sound Level</p>
            <p className="text-2xl font-bold text-blue-600">{currentDb.toFixed(1)} dB</p>
          </div>
        </div>

        {/* Live Audio Waveform */}
        <div className="mt-6">
          <p className="text-sm text-gray-500 mb-2">Live Audio Waveform</p>
          <div className="h-24 bg-gray-50 rounded-lg p-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={waveform.map((value, index) => ({ x: index, y: value }))}>
                <Line 
                  type="monotone" 
                  dataKey="y" 
                  stroke="#3B82F6" 
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Device Stats */}
      {deviceStats && (
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-green-600" />
            Device Statistics
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex items-center gap-3">
              <Thermometer className="w-5 h-5 text-orange-500" />
              <div>
                <p className="text-sm text-gray-500">Temperature</p>
                <p className="text-lg font-semibold">{deviceStats.temperature}°C</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <Cpu className="w-5 h-5 text-blue-500" />
              <div>
                <p className="text-sm text-gray-500">CPU Load</p>
                <p className="text-lg font-semibold">{deviceStats.cpu_load}%</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <Wifi className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-sm text-gray-500">WiFi Network</p>
                <p className="text-lg font-semibold">{deviceStats.wifi_ssid || 'Unknown'}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Sound Level Chart */}
      <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 text-purple-600" />
          Sound Level History
        </h2>
        
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis label={{ value: 'Sound Level (dB)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="db" 
                stroke="#8B5CF6" 
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Events */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Recent Events</h2>
        
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {events.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No events recorded yet</p>
          ) : (
            events.map((event) => (
              <div key={event.id} className="border-l-4 border-blue-500 pl-4 py-2">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-gray-900">{event.sound_type}</p>
                    <p className="text-sm text-gray-500">{event.description}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-blue-600">
                      {event.db_level?.toFixed(1) || '0.0'} dB
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
