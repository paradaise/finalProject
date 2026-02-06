import { useState } from 'react';
import { Wifi, WifiOff, Settings, Volume2, Plus, Trash2, Bell, Activity, Signal } from 'lucide-react';
import { Device } from '../api/client';
import { apiClient } from '../api/client';
import { AddDeviceModal } from './AddDeviceModal';

interface Props {
  devices: Device[];
  detections: { [key: string]: any[] };
  onSelectDevice: (deviceId: string) => void;
  onCustomSounds: () => void;
  onNotificationSettings: () => void;
}

export function DeviceList({ devices, detections, onSelectDevice, onCustomSounds, onNotificationSettings }: Props) {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [hoveredDevice, setHoveredDevice] = useState<string | null>(null);

  const handleAddDevice = () => {
    // Обновление списка устройств после добавления
    window.location.reload();
  };
  const getStatusIcon = (status: string) => {
    return status === 'online' ? (
      <Wifi className="w-5 h-5 text-green-500" />
    ) : (
      <WifiOff className="w-5 h-5 text-gray-400" />
    );
  };

  const getStatusColor = (status: string) => {
    return status === 'online' ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50';
  };

  const getWifiSignalColor = (signal: number) => {
    if (signal > 70) return 'text-green-600';
    if (signal > 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getWifiSignalBars = (signal: number) => {
    const bars = Math.max(1, Math.min(4, Math.round(signal / 25)));
    return Array(4).fill(0).map((_, i) => (
      <div
        key={i}
        className={`w-1 h-3 mx-0.5 rounded-sm ${
          i < bars ? 'bg-current' : 'bg-gray-300'
        }`}
      />
    ));
  };

  const formatLastSeen = (lastSeen: string) => {
    try {
      const date = new Date(lastSeen);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      
      if (diffMins < 1) return 'Только что';
      if (diffMins < 60) return `${diffMins} мин назад`;
      if (diffMins < 1440) return `${Math.floor(diffMins / 60)} ч назад`;
      return date.toLocaleDateString();
    } catch {
      return 'Неизвестно';
    }
  };

  const getLatestDetection = (deviceId: string) => {
    const deviceDetections = detections[deviceId] || [];
    return deviceDetections[0]; // Самая последняя детекция
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-lg shadow-lg border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4 sm:py-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3 cursor-pointer group" onClick={() => window.location.reload()}>
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg transition-transform group-hover:scale-110">
                <Activity className="w-5 h-5 sm:w-7 sm:h-7 text-white" />
              </div>
              <div>
                <h1 className="text-xl sm:text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">Sound Sentinel</h1>
                <p className="text-xs sm:text-sm text-gray-600">Мониторинг звуков в реальном времени</p>
              </div>
            </div>
            <div className="flex items-center gap-2 sm:gap-3">
              <button
                onClick={() => setIsAddModalOpen(true)}
                className="p-2 sm:p-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-700 hover:to-blue-800 shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105 active:scale-95 group"
              >
                <Plus className="w-4 h-4 sm:w-5 sm:h-5 transition-transform group-hover:rotate-90" />
              </button>
              <button
                onClick={onCustomSounds}
                className="p-2 sm:p-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-xl hover:from-purple-700 hover:to-purple-800 shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105 active:scale-95 group"
              >
                <Settings className="w-4 h-4 sm:w-5 sm:h-5 transition-transform group-hover:rotate-45" />
              </button>
              <button
                onClick={onNotificationSettings}
                className="p-2 sm:p-3 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-xl hover:from-green-700 hover:to-green-800 shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105 active:scale-95 group"
              >
                <Bell className="w-4 h-4 sm:w-5 sm:h-5 transition-transform group-hover:animate-bell" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="max-w-4xl mx-auto px-4 py-4 sm:py-6">
        <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-4 sm:p-6 shadow-xl border border-gray-100">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6">
            <div className="text-center group cursor-pointer" onClick={() => window.location.reload()}>
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center mx-auto mb-2 sm:mb-3 shadow-lg group-hover:shadow-xl transition-all duration-200 transform group-hover:scale-110">
                <Wifi className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
              </div>
              <p className="text-xs sm:text-sm text-gray-600 font-medium">Устройств онлайн</p>
              <p className="text-lg sm:text-2xl font-bold text-green-600">
                {devices.filter(d => d.status === 'online').length}/{devices.length}
              </p>
            </div>
            <div className="text-center group cursor-pointer" onClick={() => window.location.reload()}>
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center mx-auto mb-2 sm:mb-3 shadow-lg group-hover:shadow-xl transition-all duration-200 transform group-hover:scale-110">
                <Activity className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
              </div>
              <p className="text-xs sm:text-sm text-gray-600 font-medium">Всего детекций</p>
              <p className="text-lg sm:text-2xl font-bold text-blue-600">
                {Object.values(detections).reduce((sum, dets) => sum + dets.length, 0)}
              </p>
            </div>
            <div className="text-center group cursor-pointer" onClick={() => window.location.reload()}>
              <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center mx-auto mb-2 sm:mb-3 shadow-lg group-hover:shadow-xl transition-all duration-200 transform group-hover:scale-110">
                <Signal className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
              </div>
              <p className="text-xs sm:text-sm text-gray-600 font-medium">Активных устройств</p>
              <p className="text-lg sm:text-2xl font-bold text-purple-600">
                {devices.filter(d => d.status === 'online').length}
              </p>
            </div>
          </div>
        </div>

        {/* Devices List */}
        <div className="space-y-4">
          {devices.length === 0 ? (
            <div className="bg-white rounded-xl p-12 text-center shadow-sm">
              <div className="w-16 h-16 bg-gradient-to-br from-red-500 to-red-600 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-white font-bold text-xl">RP</span>
              </div>
              <h3 className="text-lg font-medium text-gray-600 mb-2">Нет устройств</h3>
              <p className="text-gray-500">Подключите Raspberry Pi для начала мониторинга</p>
            </div>
          ) : (
            devices.map((device) => {
              const latestDetection = getLatestDetection(device.id);
              return (
                <div
                  key={device.id}
                  className={`bg-white/80 backdrop-blur-lg rounded-2xl p-4 sm:p-6 shadow-xl border-2 cursor-pointer transition-all duration-300 hover:shadow-2xl transform hover:scale-[1.02] ${getStatusColor(device.status)} ${
                    hoveredDevice === device.id ? 'ring-2 ring-blue-400 ring-opacity-50' : ''
                  }`}
                  onClick={() => onSelectDevice(device.id)}
                  onMouseEnter={() => setHoveredDevice(device.id)}
                  onMouseLeave={() => setHoveredDevice(null)}
                >
                  <div className="flex flex-col sm:flex-row items-start sm:items-start justify-between gap-4">
                    <div className="flex items-start gap-3 sm:gap-4 flex-1 w-full">
                      {/* Иконка устройства */}
                      <div className="flex-shrink-0">
                        <div className="relative">
                          <img 
                            src="/images/raspberry-pi-logo-svgrepo-com.svg" 
                            alt="Raspberry Pi"
                            className={`w-12 h-12 sm:w-14 sm:h-14 rounded-2xl object-contain shadow-xl transition-all duration-300 ${
                              hoveredDevice === device.id ? 'scale-110 rotate-6' : 'scale-100 rotate-0'
                            }`}
                            onError={(e) => {
                              const target = e.currentTarget;
                              target.style.display = 'none';
                              const nextElement = target.nextElementSibling as HTMLElement;
                              if (nextElement) {
                                nextElement.style.display = 'block';
                              }
                            }}
                          />
                          <div 
                            className="w-12 h-12 sm:w-14 sm:h-14 bg-gradient-to-br from-red-500 to-red-600 rounded-2xl flex items-center justify-center shadow-xl"
                            style={{ display: 'none' }}
                          >
                            <span className="text-white font-bold text-sm sm:text-lg">RPi</span>
                          </div>
                          {device.status === 'online' && (
                            <div className="absolute -top-1 -right-1 w-3 h-3 sm:w-4 sm:h-4 bg-green-500 rounded-full border-2 border-white animate-pulse"></div>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex-1 w-full">
                        {/* Название и статус */}
                        <div className="flex items-center gap-2 sm:gap-3 mb-2">
                          {getStatusIcon(device.status)}
                          <h3 className="text-base sm:text-lg font-semibold text-gray-900">{device.name}</h3>
                        </div>
                        
                        {/* Информация об устройстве */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 text-sm mb-3">
                          <div>
                            <p className="text-gray-600 text-xs sm:text-sm">Модель</p>
                            <p className="font-medium text-gray-900 text-sm sm:text-base">{device.model}</p>
                          </div>
                          <div>
                            <p className="text-gray-600 text-xs sm:text-sm">IP адрес</p>
                            <p className="font-medium text-sm sm:text-base">{device.ip_address}</p>
                          </div>
                          <div>
                            <p className="text-gray-600 text-xs sm:text-sm">MAC адрес</p>
                            <p className="font-bold font-mono text-xs sm:text-sm">{device.mac_address}</p>
                          </div>
                          <div>
                            <p className="text-gray-600 text-xs sm:text-sm">ID устройства</p>
                            <p className="font-bold font-mono text-xs sm:text-sm break-all">{device.id}</p>
                          </div>
                          <div>
                            <p className="text-gray-600 text-xs sm:text-sm">Микрофон</p>
                            <p className="font-medium text-gray-900 text-sm sm:text-base">{device.microphone_info || 'Неизвестно'}</p>
                          </div>
                          <div>
                            <p className="text-gray-600 text-xs sm:text-sm">WiFi сигнал</p>
                            <div className="flex items-center gap-2">
                              <div className="flex items-center">
                                {getWifiSignalBars(device.wifi_signal)}
                              </div>
                              <span className={`font-medium text-sm sm:text-base ${getWifiSignalColor(device.wifi_signal)}`}>
                                {device.wifi_signal}%
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Последняя активность */}
                        <div className="text-sm text-gray-600">
                          Последняя активность: {formatLastSeen(device.last_seen)}
                        </div>

                        {/* Последняя детекция */}
                        {latestDetection && (
                          <div className="mt-3 sm:mt-4 p-3 sm:p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-100">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2 sm:gap-3">
                                <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                                  <Volume2 className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                                </div>
                                <div>
                                  <p className="text-xs sm:text-sm font-semibold text-blue-900">
                                    Последний звук: {latestDetection.sound_type}
                                  </p>
                                  <p className="text-xs text-blue-700">
                                    Уверенность: {(latestDetection.confidence * 100).toFixed(1)}%
                                  </p>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {/* Кнопка удаления */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (window.confirm(`Удалить устройство "${device.name}"?`)) {
                          apiClient.deleteDevice(device.id).then(() => {
                            window.location.reload();
                          }).catch((error: any) => {
                            console.error('Error deleting device:', error);
                            alert('Ошибка удаления устройства');
                          });
                        }
                      }}
                      className="p-2 sm:p-3 text-red-600 hover:bg-red-50 rounded-xl transition-all duration-200 hover:scale-110 shadow-md hover:shadow-lg active:scale-95 group"
                    >
                      <Trash2 className="w-4 h-4 sm:w-5 sm:h-5 transition-transform group-hover:scale-110" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Add Device Modal */}
      <AddDeviceModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onAddDevice={handleAddDevice}
      />
    </div>
  );
}
