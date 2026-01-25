import { useState, useEffect } from 'react';
import { ArrowLeft, Volume2, Clock, Activity } from 'lucide-react';
import { AudioLevelChart } from './AudioLevelChart';
import { apiClient } from '../api/client';

interface Props {
  deviceId: string;
  onBack: () => void;
}

export function DeviceDetail({ deviceId, onBack }: Props) {
  const [device, setDevice] = useState<any>(null);
  const [detections, setDetections] = useState<any[]>([]);
  const [currentSound, setCurrentSound] = useState<any>(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDeviceData();
    
    // Подписываемся на WebSocket обновления
    const ws = apiClient.connectWebSocket((data: any) => {
      if (data.device_id === deviceId) {
        if (data.type === 'sound_detected') {
          setCurrentSound({
            sound_type: data.sound_type,
            confidence: data.confidence,
            timestamp: data.timestamp
          });
          
          // Добавляем новую детекцию в начало списка
          setDetections(prev => [data, ...prev.slice(0, 49)]);
          
          // Обновляем уровень звука (симуляция)
          setAudioLevel(Math.random() * 60 + 20); // 20-80 dB
        }
      }
    });

    return () => {
      ws.close();
    };
  }, [deviceId]);

  const loadDeviceData = async () => {
    try {
      setLoading(true);
      
      // Загружаем информацию об устройстве
      const devices = await apiClient.getDevices();
      const currentDevice = devices.find(d => d.id === deviceId);
      setDevice(currentDevice);

      // Загружаем детекции
      const deviceDetections = await apiClient.getDeviceEvents(deviceId, 50);
      setDetections(deviceDetections);
      
      if (deviceDetections.length > 0) {
        setCurrentSound(deviceDetections[0]);
      }
    } catch (error) {
      console.error('Error loading device data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('ru-RU');
    } catch {
      return timestamp;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence > 0.7) return 'text-green-600 bg-green-50';
    if (confidence > 0.4) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка...</p>
        </div>
      </div>
    );
  }

  if (!device) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Устройство не найдено</p>
          <button
            onClick={onBack}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Назад
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-xl font-semibold">{device.name}</h1>
              <p className="text-sm text-gray-600">{device.ip_address}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Stats */}
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Статус</p>
              <p className="text-lg font-semibold text-green-600">
                {device.status === 'online' ? 'Онлайн' : 'Офлайн'}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Детекций</p>
              <p className="text-lg font-semibold text-blue-600">{detections.length}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Последняя активность</p>
              <p className="text-lg font-semibold">
                {device.last_seen ? formatTime(device.last_seen) : 'Нет данных'}
              </p>
            </div>
          </div>
        </div>

        {/* Текущий звук */}
        {currentSound && (
          <div className="bg-white rounded-xl p-6 shadow-sm border-l-4 border-blue-500">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Volume2 className="w-6 h-6 text-blue-600" />
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {currentSound.sound_type}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {formatTime(currentSound.timestamp)}
                  </p>
                </div>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getConfidenceColor(currentSound.confidence)}`}>
                {(currentSound.confidence * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        )}

        {/* График уровня звука */}
        <AudioLevelChart deviceId={deviceId} currentLevel={audioLevel} />

        {/* История детекций */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">История детекций</h2>
          
          {detections.length === 0 ? (
            <div className="bg-white rounded-xl p-12 text-center shadow-sm">
              <Activity className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-600 mb-2">Нет детекций</h3>
              <p className="text-gray-500">Звуки еще не были обнаружены</p>
            </div>
          ) : (
            <div className="space-y-3">
              {detections.map((detection) => (
                <div
                  key={detection.id}
                  className="bg-white rounded-xl p-4 shadow-sm border-l-4 border-blue-500"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <Volume2 className="w-5 h-5 text-blue-600" />
                        <h3 className="font-semibold text-gray-900">
                          {detection.sound_type}
                        </h3>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(detection.confidence)}`}>
                          {(detection.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Clock className="w-4 h-4" />
                        <span>{formatTime(detection.timestamp)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
