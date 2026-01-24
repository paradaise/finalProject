import React, { useState, useEffect } from 'react';
import { DeviceList } from './components/DeviceList';
import { DeviceDetail } from './components/DeviceDetail';
import { CustomSounds } from './components/CustomSounds';
import { apiClient } from './api/client';

type Screen = 'devices' | 'device-detail' | 'custom-sounds';

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
      console.log('WebSocket received:', data);
      
      if (data.type === 'device_registered') {
        setDevices(prev => [...prev, {
          id: data.device_id,
          name: data.name,
          status: data.status,
          ip_address: '',
          last_seen: new Date().toISOString()
        }]);
      } else if (data.type === 'sound_detected') {
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
      
      // Загрузка детекций для каждого устройства
      const detectionsData: { [key: string]: any[] } = {};
      for (const device of devicesData) {
        const deviceDetections = await apiClient.getDetections(device.id, 20);
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

  const handleBack = () => {
    setSelectedDeviceId(null);
    setCurrentScreen('devices');
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 mb-4">⚠️ {error}</div>
          <button 
            onClick={loadData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  // Main render
  return (
    <div className="min-h-screen bg-gray-50">
      {currentScreen === 'devices' && (
        <DeviceList
          devices={devices}
          detections={detections}
          onSelectDevice={handleSelectDevice}
          onCustomSounds={() => setCurrentScreen('custom-sounds')}
        />
      )}
      
      {currentScreen === 'device-detail' && selectedDeviceId && (
        <DeviceDetail
          deviceId={selectedDeviceId}
          device={devices.find(d => d.id === selectedDeviceId)}
          detections={detections[selectedDeviceId] || []}
          onBack={handleBack}
        />
      )}
      
      {currentScreen === 'custom-sounds' && (
        <CustomSounds
          sounds={customSounds}
          onBack={handleBack}
          onRefresh={loadData}
        />
      )}
    </div>
  );
}
