import { useState, useEffect } from 'react';
import { DeviceListScreen } from './components/DeviceListScreen';
import { DeviceDetailsScreen } from './components/DeviceDetailsScreen';
import { ExcludingSoundsScreen } from './components/ExcludingSoundsScreen';
import { SpecificSoundsScreen } from './components/SpecificSoundsScreen';
import { apiClient, Device, AudioEvent, ExcludedSound, SpecificSound } from './api/client';

export type Screen = 'deviceList' | 'deviceDetails' | 'excludingSounds' | 'specificSounds';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('deviceList');
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Реальные данные с API
  const [devices, setDevices] = useState<Device[]>([]);
  const [audioEvents, setAudioEvents] = useState<{ [deviceId: string]: AudioEvent[] }>({});
  const [excludedSounds, setExcludedSounds] = useState<ExcludedSound[]>([]);
  const [specificSounds, setSpecificSounds] = useState<SpecificSound[]>([]);

  // Загрузка начальных данных
  useEffect(() => {
    loadInitialData();
    
    // Подключение WebSocket для реального времени
    apiClient.connectWebSocket((event: AudioEvent) => {
      setAudioEvents((prev: { [deviceId: string]: AudioEvent[] }) => ({
        ...prev,
        [event.device_id]: [event, ...(prev[event.device_id] || [])].slice(0, 100)
      }));
    });

    return () => {
      apiClient.disconnectWebSocket();
    };
  }, []);

  const loadInitialData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Загрузка устройств
      const devicesData = await apiClient.getDevices();
      setDevices(devicesData);
      
      // Загрузка событий для каждого устройства
      const eventsData: { [deviceId: string]: AudioEvent[] } = {};
      for (const device of devicesData) {
        const events = await apiClient.getDeviceEvents(device.id, 50);
        eventsData[device.id] = events;
      }
      setAudioEvents(eventsData);
      
      // Загрузка пользовательских звуков
      const customSounds = await apiClient.getCustomSounds();
      setExcludedSounds(customSounds.filter(s => s.sound_type === 'excluded').map(s => ({
        id: s.id,
        name: s.name,
        icon: getIconForSound(s.name),
        recordedAt: new Date(s.created_at),
        duration: 0 // Будем вычислять позже
      })));
      
      setSpecificSounds(customSounds.filter(s => s.sound_type === 'specific').map(s => ({
        id: s.id,
        name: s.name,
        icon: getIconForSound(s.name),
        priority: 'medium' as const,
        recordedAt: new Date(s.created_at),
        duration: 0 // Будем вычислять позже
      })));
      
    } catch (err) {
      setError('Ошибка загрузки данных. Проверьте подключение к API серверу.');
      console.error('Error loading initial data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const getIconForSound = (soundName: string): string => {
    const name = soundName.toLowerCase();
    if (name.includes('door') || name.includes('bell')) return 'bell';
    if (name.includes('baby') || name.includes('cry')) return 'baby';
    if (name.includes('dog')) return 'dog';
    if (name.includes('glass')) return 'alert-triangle';
    if (name.includes('water') || name.includes('tap')) return 'droplet';
    if (name.includes('alarm') || name.includes('siren')) return 'alert';
    if (name.includes('phone')) return 'phone';
    return 'volume-2';
  };

  const handleSelectDevice = (deviceId: string) => {
    setSelectedDeviceId(deviceId);
    setCurrentScreen('deviceDetails');
  };

  const handleAddDevice = async (device: Omit<Device, 'id' | 'last_seen'>) => {
    try {
      const newDevice = await apiClient.registerDevice(device);
      setDevices([...devices, newDevice]);
    } catch (error) {
      console.error('Error adding device:', error);
      setError('Ошибка добавления устройства');
    }
  };

  const handleDeleteDevice = async (deviceId: string) => {
    try {
      await apiClient.deleteDevice(deviceId);
      setDevices(devices.filter((d: Device) => d.id !== deviceId));
      if (selectedDeviceId === deviceId) {
        setSelectedDeviceId(null);
        setCurrentScreen('deviceList');
      }
    } catch (error) {
      console.error('Error deleting device:', error);
      setError('Ошибка удаления устройства');
    }
  };

  const handleAddExcludedSound = async (sound: Omit<ExcludedSound, 'id'>) => {
    try {
      // Здесь нужна логика записи аудио и извлечения MFCC
      // Пока используем заглушку
      const mfccFeatures = new Array(13).fill(0); // Заглушка MFCC
      const deviceId = selectedDeviceId || devices[0]?.id || '';
      
      await apiClient.addCustomSound(sound.name, 'excluded', mfccFeatures, deviceId);
      
      const newSound: ExcludedSound = {
        ...sound,
        id: Date.now().toString(),
      };
      setExcludedSounds([...excludedSounds, newSound]);
    } catch (error) {
      console.error('Error adding excluded sound:', error);
      setError('Ошибка добавления исключенного звука');
    }
  };

  const handleDeleteExcludedSound = async (soundId: string) => {
    try {
      await apiClient.deleteCustomSound(soundId);
      setExcludedSounds(excludedSounds.filter((s: ExcludedSound) => s.id !== soundId));
    } catch (error) {
      console.error('Error deleting excluded sound:', error);
      setError('Ошибка удаления исключенного звука');
    }
  };

  const handleAddSpecificSound = async (sound: Omit<SpecificSound, 'id'>) => {
    try {
      // Здесь нужна логика записи аудио и извлечения MFCC
      const mfccFeatures = new Array(13).fill(0); // Заглушка MFCC
      const deviceId = selectedDeviceId || devices[0]?.id || '';
      
      await apiClient.addCustomSound(sound.name, 'specific', mfccFeatures, deviceId);
      
      const newSound: SpecificSound = {
        ...sound,
        id: Date.now().toString(),
      };
      setSpecificSounds([...specificSounds, newSound]);
    } catch (error) {
      console.error('Error adding specific sound:', error);
      setError('Ошибка добавления специфического звука');
    }
  };

  const handleDeleteSpecificSound = async (soundId: string) => {
    try {
      await apiClient.deleteCustomSound(soundId);
      setSpecificSounds(specificSounds.filter((s: SpecificSound) => s.id !== soundId));
    } catch (error) {
      console.error('Error deleting specific sound:', error);
      setError('Ошибка удаления специфического звука');
    }
  };

  const selectedDevice = devices.find((d: Device) => d.id === selectedDeviceId);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка данных...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-gray-800 font-medium mb-2">{error}</p>
          <button 
            onClick={loadInitialData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {currentScreen === 'deviceList' && (
        <DeviceListScreen
          devices={devices}
          selectedDeviceId={selectedDeviceId}
          onSelectDevice={handleSelectDevice}
          onAddDevice={handleAddDevice}
          onDeleteDevice={handleDeleteDevice}
          audioEvents={audioEvents}
        />
      )}
      
      {currentScreen === 'deviceDetails' && selectedDevice && (
        <DeviceDetailsScreen
          device={selectedDevice}
          onBack={() => setCurrentScreen('deviceList')}
          onNavigateToExcludingSounds={() => setCurrentScreen('excludingSounds')}
          onNavigateToSpecificSounds={() => setCurrentScreen('specificSounds')}
          audioEvents={audioEvents[selectedDevice.id] || []}
        />
      )}
      
      {currentScreen === 'excludingSounds' && (
        <ExcludingSoundsScreen
          excludedSounds={excludedSounds}
          onBack={() => setCurrentScreen('deviceDetails')}
          onAddSound={handleAddExcludedSound}
          onDeleteSound={handleDeleteExcludedSound}
        />
      )}
      
      {currentScreen === 'specificSounds' && (
        <SpecificSoundsScreen
          specificSounds={specificSounds}
          onBack={() => setCurrentScreen('deviceDetails')}
          onAddSound={handleAddSpecificSound}
          onDeleteSound={handleDeleteSpecificSound}
        />
      )}
    </div>
  );
}
