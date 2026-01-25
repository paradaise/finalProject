import React from 'react';
import { Wifi, WifiOff, Settings, Volume2, Plus, Trash2, Bell } from 'lucide-react';
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
  const [isAddModalOpen, setIsAddModalOpen] = React.useState(false);

  const handleAddDevice = (newDevice: any) => {
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

  const onlineCount = devices.filter(d => d.status === 'online').length;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Sound Sentinel</h1>
              <p className="text-sm text-gray-600">Мониторинг звуков в реальном времени</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsAddModalOpen(true)}
                className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="w-5 h-5" />
              </button>
              <button
                onClick={onCustomSounds}
                className="p-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                <Settings className="w-5 h-5" />
              </button>
              <button
                onClick={onNotificationSettings}
                className="p-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                <Bell className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Устройств онлайн</p>
              <p className="text-lg font-semibold text-green-600">
                {devices.filter(d => d.status === 'online').length}/{devices.length}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Всего детекций</p>
              <p className="text-lg font-semibold text-blue-600">
                {Object.values(detections).reduce((sum, dets) => sum + dets.length, 0)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Активных устройств</p>
              <p className="text-lg font-semibold text-purple-600">
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
                  className={`bg-white rounded-xl p-6 shadow-sm border-2 cursor-pointer transition-all hover:shadow-md ${getStatusColor(device.status)}`}
                  onClick={() => onSelectDevice(device.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4 flex-1">
                      {/* Иконка устройства */}
                      <div className="flex-shrink-0">
                        <img 
                          src="/images/raspberry-pi-logo-svgrepo-com.svg" 
                          alt="Raspberry Pi"
                          className="w-12 h-12 rounded-lg object-contain shadow-lg hover:scale-110 transition-transform duration-200"
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
                          className="w-12 h-12 bg-gradient-to-br from-red-500 to-red-600 rounded-lg flex items-center justify-center shadow-lg"
                          style={{ display: 'none' }}
                        >
                          <span className="text-white font-bold text-lg">RPi</span>
                        </div>
                      </div>
                      
                      <div className="flex-1">
                        {/* Название и статус */}
                        <div className="flex items-center gap-3 mb-2">
                          {getStatusIcon(device.status)}
                          <h3 className="text-lg font-semibold text-gray-900">{device.name}</h3>
                        </div>
                        
                        {/* Информация об устройстве */}
                        <div className="grid grid-cols-2 gap-4 text-sm mb-3">
                          <div>
                            <p className="text-gray-600">Модель</p>
                            <p className="font-medium text-gray-900">{device.model}</p>
                          </div>
                          <div>
                            <p className="text-gray-600">IP адрес</p>
                            <p className="font-medium">{device.ip_address}</p>
                          </div>
                          <div>
                            <p className="text-gray-600">MAC адрес</p>
                            <p className="font-bold font-mono text-sm">{device.mac_address}</p>
                          </div>
                          <div>
                            <p className="text-gray-600">ID устройства</p>
                            <p className="font-bold font-mono text-sm">{device.id}</p>
                          </div>
                          <div>
                            <p className="text-gray-600">Микрофон</p>
                            <p className="font-medium text-gray-900">{device.microphone_info || 'Неизвестно'}</p>
                          </div>
                          <div>
                            <p className="text-gray-600">WiFi сигнал</p>
                            <div className="flex items-center gap-2">
                              <div className="flex items-center">
                                {getWifiSignalBars(device.wifi_signal)}
                              </div>
                              <span className={`font-medium ${getWifiSignalColor(device.wifi_signal)}`}>
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
                          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-sm font-medium text-blue-900">
                                  Последний звук: {latestDetection.sound_type}
                                </p>
                                <p className="text-xs text-blue-700">
                                  Уверенность: {(latestDetection.confidence * 100).toFixed(1)}%
                                </p>
                              </div>
                              <Volume2 className="w-5 h-5 text-blue-600" />
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
                            // Обновляем список устройств
                            window.location.reload();
                          }).catch((error: any) => {
                            console.error('Error deleting device:', error);
                            alert('Ошибка удаления устройства');
                          });
                        }
                      }}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
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
