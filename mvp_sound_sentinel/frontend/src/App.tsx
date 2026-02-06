import { useState, useEffect } from 'react';
import { DeviceList } from './components/DeviceList';
import { DeviceDetail } from './components/DeviceDetail';
import { CustomSounds } from './components/CustomSounds';
import { NotificationSettings } from './components/NotificationSettings';
import { ImprovedNotificationManager } from './components/ImprovedNotifications';
import { Activity } from 'lucide-react';
import { apiClient } from './api/client';

type Screen = 'devices' | 'device-detail' | 'custom-sounds' | 'notification-settings';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('devices');
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
  const [devices, setDevices] = useState<any[]>([]);
  const [detections, setDetections] = useState<{ [key: string]: any[] }>({});
  const [customSounds, setCustomSounds] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Загрузка данных
  useEffect(() => {
    loadData();
    
    // WebSocket для реального времени
    const ws = apiClient.connectWebSocket((data) => {
      console.log('📡 WebSocket received:', data);
      
      if (data.type === 'device_registered') {
        setDevices(prev => [...prev, {
          id: data.device_id,
          name: data.name,
          status: data.status,
          ip_address: '',
          last_seen: new Date().toISOString()
        }]);
      } else if (data.type === 'sound_detected') {
        console.log('🔊 Sound detected in App:', {
          sound_type: data.sound_type,
          confidence: data.confidence,
          should_notify: data.should_notify
        });
        
        setDetections(prev => ({
          ...prev,
          [data.device_id]: [
            {
              id: data.detection_id,
              sound_type: data.sound_type,
              confidence: data.confidence,
              timestamp: data.timestamp
            },
            ...(prev[data.device_id] || [])
          ].slice(0, 50)
        }));
        
        // Отправляем событие для уведомлений
        console.log('📤 Dispatching soundDetected event with:', data);
        window.dispatchEvent(new CustomEvent('soundDetected', { detail: data }));
      } else if (data.type === 'audio_level_updated') {
        // Пробрасываем событие уровня звука для компонентов, которым это нужно (например, графику в DeviceDetail)
        window.dispatchEvent(new CustomEvent('audioLevelUpdated', { detail: data }));
      }
    });

    return () => {
      ws.close();
    };
  }, []);

  const loadData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Загрузка устройств
      const devicesData = await apiClient.getDevices();
      setDevices(devicesData);
      
      // Загрузка детекций для каждого устройства (убираем ограничение)
      const detectionsData: { [key: string]: any[] } = {};
      for (const device of devicesData) {
        const deviceDetections = await apiClient.getDeviceEvents(device.id, 1000);
        detectionsData[device.id] = deviceDetections;
      }
      setDetections(detectionsData);
      
      // Загрузка пользовательских звуков
      const soundsData = await apiClient.getCustomSounds();
      setCustomSounds(soundsData);
      
    } catch (err) {
      setError('Ошибка загрузки данных. Проверьте подключение к API.');
      console.error('Load data error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectDevice = (deviceId: string) => {
    setSelectedDeviceId(deviceId);
    setCurrentScreen('device-detail');
  };

  const handleCustomSounds = () => {
    // Если есть только одно устройство, выбираем его автоматически
    if (devices.length === 1) {
      setSelectedDeviceId(devices[0].id);
    } else if (devices.length > 1 && !selectedDeviceId) {
      // Если устройств несколько и ничего не выбрано, выбираем первое
      setSelectedDeviceId(devices[0].id);
    }
    setCurrentScreen('custom-sounds');
  };

  const handleBack = () => {
    setSelectedDeviceId(null);
    setCurrentScreen('devices');
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center px-4">
          <div className="relative">
            <div className="w-12 h-12 sm:w-16 sm:h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-4 sm:mb-6 shadow-xl">
              <Activity className="w-6 h-6 sm:w-8 sm:h-8 text-white" />
            </div>
            <div className="absolute inset-0 w-12 h-12 sm:w-16 sm:h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center mx-auto animate-ping opacity-20"></div>
          </div>
          <div className="animate-spin rounded-full h-6 w-6 sm:h-8 sm:w-8 border-b-2 border-blue-600 mx-auto mb-3 sm:mb-4"></div>
          <p className="text-gray-600 font-medium text-sm sm:text-base">Загрузка Sound Sentinel...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center px-4">
          <div className="w-12 h-12 sm:w-16 sm:h-16 bg-gradient-to-br from-red-500 to-red-600 rounded-2xl flex items-center justify-center mx-auto mb-4 sm:mb-6 shadow-xl">
            <span className="text-white font-bold text-xl sm:text-2xl">!</span>
          </div>
          <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-4 sm:p-6 shadow-xl border border-gray-100 max-w-sm sm:max-w-md">
            <h3 className="text-base sm:text-lg font-bold text-red-600 mb-2">Ошибка подключения</h3>
            <p className="text-gray-600 text-sm sm:text-base mb-4">{error}</p>
            <button 
              onClick={loadData}
              className="px-4 py-2 sm:px-6 sm:py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-700 hover:to-blue-800 shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105 active:scale-95 font-medium text-sm sm:text-base group"
            >
              Попробовать снова
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Main render
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Уведомления */}
      <ImprovedNotificationManager
        onSoundDetected={(data: any) => {
          // Обработка звуковых событий для обновления детекций
          if (data.type === 'sound_detected') {
            setDetections(prev => ({
              ...prev,
              [data.device_id]: [
                {
                  id: data.detection_id,
                  sound_type: data.sound_type,
                  confidence: data.confidence,
                  timestamp: data.timestamp
                },
                ...(prev[data.device_id] || [])
              ].slice(0, 50)
            }));
          }
        }}
      />
      
      {currentScreen === 'devices' && (
        <DeviceList
          devices={devices}
          detections={detections}
          onSelectDevice={handleSelectDevice}
          onCustomSounds={handleCustomSounds}
          onNotificationSettings={() => setCurrentScreen('notification-settings')}
        />
      )}
      
      {currentScreen === 'device-detail' && selectedDeviceId && (
        <DeviceDetail
          deviceId={selectedDeviceId}
          onBack={handleBack}
        />
      )}
      
      {currentScreen === 'custom-sounds' && (
        <CustomSounds 
          sounds={customSounds}
          onBack={() => setCurrentScreen('devices')}
          onRefresh={loadData}
          selectedDeviceId={selectedDeviceId || undefined}
        />
      )}
      
      {currentScreen === 'notification-settings' && (
        <NotificationSettings 
          onBack={() => setCurrentScreen('devices')}
        />
      )}
    </div>
  );
}
