import { useState, useEffect } from 'react';
import { Wifi, Volume2, Clock, Activity, Mic, Globe, ArrowLeft, Cpu, Trash2 } from 'lucide-react';
import { apiClient } from '../api/client';
import { getSoundIcon } from '../data/criticalSounds';
import { AudioLevelChart } from './AudioLevelChart';

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
    
    // Подписываемся на системные события (уровень звука и детекции)
    const handleAudioLevel = (event: any) => {
      const data = event.detail;
      if (data.device_id === deviceId) {
        setAudioLevel(data.db_level);
      }
    };

    const handleSoundDetected = (event: any) => {
      const data = event.detail;
      if (data.device_id === deviceId) {
        setCurrentSound({
          sound_type: data.sound_type,
          confidence: data.confidence,
          timestamp: data.timestamp
        });
        
        setDetections(prev => {
          const isDuplicate = prev.length > 0 && 
            prev[0].sound_type === data.sound_type && 
            prev[0].confidence === data.confidence &&
            Math.abs(new Date(prev[0].timestamp).getTime() - new Date(data.timestamp).getTime()) < 1000;
          
          if (!isDuplicate) {
            return [data, ...prev.slice(0, 49)];
          }
          return prev;
        });
      }
    };

    window.addEventListener('audioLevelUpdated', handleAudioLevel);
    window.addEventListener('soundDetected', handleSoundDetected);
    
    // Подписываемся на WebSocket обновления для системных событий устройства
    const ws = apiClient.connectWebSocket((data: any) => {
      if (data.device_id === deviceId) {
        // Обновление информации об устройстве (включая WiFi)
        if (data.type === 'device_updated') {
          setDevice((prev: any) => prev ? { ...prev, ...data.device_info } : null);
        }
      }
    });

    return () => {
      window.removeEventListener('audioLevelUpdated', handleAudioLevel);
      window.removeEventListener('soundDetected', handleSoundDetected);
      ws.close();
    };
  }, [deviceId]);

  const handleClearDetections = async () => {
    if (window.confirm(`Вы уверены, что хотите очистить всю историю детекций для устройства "${device.name}"?`)) {
      try {
        await apiClient.clearDeviceDetections(deviceId);
        setDetections([]);
        setCurrentSound(null);
      } catch (error) {
        console.error('Error clearing detections:', error);
        alert('Не удалось очистить историю детекций.');
      }
    }
  };

  const loadDeviceData = async () => {
    try {
      setLoading(true);
      
      // Загружаем информацию об устройстве
      const devices = await apiClient.getDevices();
      const currentDevice = devices.find(d => d.id === deviceId);
      setDevice(currentDevice);

      // Загружаем детекции (получаем общее количество)
      const deviceDetections = await apiClient.getDeviceEvents(deviceId, 1000);
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
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-lg shadow-lg border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4 sm:py-6">
            <div className="flex items-center gap-3 sm:gap-4">
              <button
                onClick={onBack}
                className="p-2 sm:p-3 hover:bg-gray-100 rounded-xl transition-all duration-200 hover:scale-105 shadow-md hover:shadow-lg active:scale-95 group"
              >
                <ArrowLeft className="w-4 h-4 sm:w-5 sm:h-5 transition-transform group-hover:-translate-x-1" />
              </button>
              <div className="flex items-center gap-3 sm:gap-4 cursor-pointer group" onClick={() => window.location.reload()}>
                <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg transition-transform group-hover:scale-110 cursor-pointer">
                  <Activity className="w-5 h-5 sm:w-7 sm:h-7 text-white" />
                </div>
                <div>
                  <h1 className="text-lg sm:text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent cursor-pointer">{device.name}</h1>
                  <p className="text-xs sm:text-sm text-gray-600">{device.ip_address}</p>
                </div>
              </div>
            </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-4 sm:py-6 space-y-4 sm:space-y-6">
        {/* Device Info */}
        <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-4 sm:p-6 shadow-xl border border-gray-100">
          <h2 className="text-lg sm:text-xl font-bold mb-4 sm:mb-6 bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">Информация об устройстве</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
            <div className="flex items-center gap-3 p-3 sm:p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-100 group hover:shadow-lg transition-all duration-200 cursor-pointer">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg transition-all duration-200">
                <Cpu className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
              </div>
              <div>
                <p className="text-xs text-gray-600 font-medium">Модель</p>
                <p className="font-semibold text-gray-900 text-sm sm:text-base">{device.model}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 sm:p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-100 group hover:shadow-lg transition-all duration-200 cursor-pointer">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg transition-all duration-200">
                <Globe className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
              </div>
              <div>
                <p className="text-xs text-gray-600 font-medium">IP адрес</p>
                <p className="font-semibold text-gray-900 text-sm sm:text-base">{device.ip_address}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 sm:p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl border border-purple-100 group hover:shadow-lg transition-all duration-200 cursor-pointer">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg transition-all duration-200">
                <Activity className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
              </div>
              <div>
                <p className="text-xs text-gray-600 font-medium">MAC адрес</p>
                <p className="font-bold font-mono text-xs sm:text-sm text-gray-900 break-all">{device.mac_address}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 sm:p-4 bg-gradient-to-r from-orange-50 to-red-50 rounded-xl border border-orange-100 group hover:shadow-lg transition-all duration-200 cursor-pointer">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg transition-all duration-200">
                <Mic className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
              </div>
              <div>
                <p className="text-xs text-gray-600 font-medium">Микрофон</p>
                <p className="font-semibold text-gray-900 text-sm sm:text-base">{device.microphone_info || 'Неизвестно'}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 sm:p-4 bg-gradient-to-r from-cyan-50 to-blue-50 rounded-xl border border-cyan-100 group hover:shadow-lg transition-all duration-200 cursor-pointer">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg transition-all duration-200">
                <Wifi className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
              </div>
              <div>
                <p className="text-xs text-gray-600 font-medium">WiFi сигнал</p>
                <p className="font-semibold text-gray-900 text-sm sm:text-base">{device.wifi_signal}%</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 sm:p-4 bg-gradient-to-r from-gray-50 to-slate-50 rounded-xl border border-gray-200 group hover:shadow-lg transition-all duration-200 cursor-pointer">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-gray-500 to-gray-600 rounded-xl flex items-center justify-center shadow-md group-hover:shadow-lg transition-all duration-200">
                <Clock className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
              </div>
              <div>
                <p className="text-xs text-gray-600 font-medium">ID устройства</p>
                <p className="font-bold font-mono text-xs sm:text-sm text-gray-900 break-all">{device.id}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-4 sm:p-6 shadow-xl border border-gray-100">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
            <div className="text-center p-3 sm:p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-100 cursor-pointer">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center mx-auto mb-2 sm:mb-3 shadow-lg">
                <Wifi className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
              </div>
              <p className="text-xs sm:text-sm text-gray-600 font-medium mb-1">Статус</p>
              <p className="text-lg sm:text-xl font-bold text-green-600">
                {device.status === 'online' ? 'Онлайн' : 'Офлайн'}
              </p>
            </div>
            <div className="text-center p-3 sm:p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-100 cursor-pointer">
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center mx-auto mb-2 sm:mb-3 shadow-lg">
                <Clock className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
              </div>
              <p className="text-xs sm:text-sm text-gray-600 font-medium mb-1">Последняя активность</p>
              <p className="text-lg sm:text-xl font-bold text-blue-600">
                {device.last_seen ? formatTime(device.last_seen) : 'Нет данных'}
              </p>
            </div>
          </div>
        </div>

        {/* Текущий звук */}
        {currentSound && (
          <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-4 sm:p-6 shadow-xl border-l-4 border-blue-500 border border-gray-100">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3 sm:gap-4">
                <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg animate-pulse">
                  <Volume2 className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-lg sm:text-xl font-bold text-gray-900">
                    {currentSound.sound_type}
                  </h3>
                  <p className="text-xs sm:text-sm text-gray-600">
                    {formatTime(currentSound.timestamp)}
                  </p>
                </div>
              </div>
              <span className={`px-3 py-1 sm:px-4 sm:py-2 rounded-full text-xs sm:text-sm font-bold shadow-md ${getConfidenceColor(currentSound.confidence)}`}>
                {(currentSound.confidence * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        )}

        {/* График уровня звука */}
        <AudioLevelChart currentLevel={audioLevel} />

        {/* История детекций */}
        <div className="space-y-4 sm:space-y-6">
          <h2 className="text-lg sm:text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">История детекций</h2>
          
          {detections.length === 0 ? (
            <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-8 sm:p-12 text-center shadow-xl border border-gray-100">
              <div className="w-16 h-16 sm:w-20 sm:h-20 bg-gradient-to-br from-gray-400 to-gray-500 rounded-2xl flex items-center justify-center mx-auto mb-4 sm:mb-6 shadow-lg">
                <Activity className="w-8 h-8 sm:w-10 sm:h-10 text-white" />
              </div>
              <h3 className="text-lg sm:text-xl font-bold text-gray-600 mb-2">Нет детекций</h3>
              <p className="text-gray-500 text-sm sm:text-base">Звуки еще не были обнаружены</p>
            </div>
          ) : (
            <div className="space-y-3 sm:space-y-4">
              {detections.slice(0, 50).map((detection, index) => (
                <div
                  key={detection.id}
                  className="bg-white/80 backdrop-blur-lg rounded-2xl p-3 sm:p-4 shadow-xl border-l-4 border-blue-500 border border-gray-100 transition-all duration-300 hover:shadow-2xl hover:scale-[1.02]"
                  style={{
                    animationDelay: `${index * 50}ms`
                  }}
                >
                  <div className="flex flex-col sm:flex-row items-start justify-between gap-3">
                    <div className="flex-1 w-full">
                      <div className="flex items-start gap-2 sm:gap-3 mb-2">
                        <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg flex-shrink-0">
                          <span className="text-lg sm:text-xl">{getSoundIcon(detection.sound_type)}</span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-bold text-gray-900 text-sm sm:text-lg mb-1">
                            {detection.sound_type}
                          </h3>
                          <p className="text-xs sm:text-sm text-gray-600">
                            {formatTime(detection.timestamp)}
                          </p>
                        </div>
                        <span className={`px-2 py-1 sm:px-3 sm:py-1 rounded-full text-xs font-bold shadow-md flex-shrink-0 ${getConfidenceColor(detection.confidence)}`}>
                          {(detection.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              {detections.length > 0 && (
                <div className="flex items-center justify-between text-center py-4 sm:py-6 bg-white/80 backdrop-blur-lg rounded-2xl shadow-xl border border-gray-100 px-6">
                  <p className="text-gray-500 text-xs sm:text-sm font-medium">
                    Показано {Math.min(50, detections.length)} из {detections.length} детекций
                  </p>
                  <button
                    onClick={handleClearDetections}
                    className="p-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors shadow-md"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
