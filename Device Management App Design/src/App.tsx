import { useState } from 'react';
import { DeviceListScreen } from './components/DeviceListScreen';
import { DeviceDetailsScreen } from './components/DeviceDetailsScreen';
import { ExcludingSoundsScreen } from './components/ExcludingSoundsScreen';
import { SpecificSoundsScreen } from './components/SpecificSoundsScreen';

export type Device = {
  id: string;
  name: string;
  ipAddress: string;
  macAddress: string;
  status: 'online' | 'offline' | 'error';
  lastSeen: Date;
  temperature?: number;
  cpuLoad?: number;
  imageUrl?: string;
};

export type AudioEvent = {
  id: string;
  type: 'voice' | 'noise' | 'music' | 'alarm' | 'unknown';
  timestamp: Date;
  intensity: number;
  description: string;
};

export type ExcludedSound = {
  id: string;
  name: string;
  icon: string;
  recordedAt: Date;
  duration: number;
};

export type SpecificSound = {
  id: string;
  name: string;
  icon: string;
  priority: 'low' | 'medium' | 'high';
  recordedAt: Date;
  duration: number;
};

export type Screen = 'deviceList' | 'deviceDetails' | 'excludingSounds' | 'specificSounds';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('deviceList');
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);

  const [devices, setDevices] = useState<Device[]>([
    {
      id: '1',
      name: 'Living Room Monitor',
      ipAddress: '192.168.1.101',
      macAddress: 'B8:27:EB:A4:5C:2D',
      status: 'online',
      lastSeen: new Date(),
      temperature: 42,
      cpuLoad: 23,
    },
    {
      id: '2',
      name: 'Bedroom Monitor',
      ipAddress: '192.168.1.102',
      macAddress: 'B8:27:EB:C3:7A:1F',
      status: 'online',
      lastSeen: new Date(),
      temperature: 38,
      cpuLoad: 18,
    },
    {
      id: '3',
      name: 'Kitchen Monitor',
      ipAddress: '192.168.1.103',
      macAddress: 'B8:27:EB:D2:9B:4E',
      status: 'error',
      lastSeen: new Date(Date.now() - 1000 * 60 * 15),
      temperature: 45,
      cpuLoad: 67,
    },
    {
      id: '4',
      name: 'Garage Monitor',
      ipAddress: '192.168.1.104',
      macAddress: 'B8:27:EB:E1:2C:8A',
      status: 'offline',
      lastSeen: new Date(Date.now() - 1000 * 60 * 60 * 2),
    },
  ]);

  const [excludedSounds, setExcludedSounds] = useState<ExcludedSound[]>([
    {
      id: '1',
      name: 'Refrigerator Hum',
      icon: 'radio',
      recordedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2),
      duration: 5.2,
    },
    {
      id: '2',
      name: 'Air Conditioner',
      icon: 'wind',
      recordedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5),
      duration: 8.1,
    },
    {
      id: '3',
      name: 'Clock Ticking',
      icon: 'clock',
      recordedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 10),
      duration: 3.5,
    },
  ]);

  const [specificSounds, setSpecificSounds] = useState<SpecificSound[]>([
    {
      id: '1',
      name: 'Baby Crying',
      icon: 'baby',
      priority: 'high',
      recordedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3),
      duration: 4.2,
    },
    {
      id: '2',
      name: 'Doorbell',
      icon: 'bell',
      priority: 'high',
      recordedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 7),
      duration: 2.1,
    },
    {
      id: '3',
      name: 'Glass Breaking',
      icon: 'alert-triangle',
      priority: 'high',
      recordedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 14),
      duration: 1.8,
    },
    {
      id: '4',
      name: 'Dog Barking',
      icon: 'dog',
      priority: 'medium',
      recordedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 1),
      duration: 3.3,
    },
  ]);

  const handleSelectDevice = (deviceId: string) => {
    setSelectedDeviceId(deviceId);
    setCurrentScreen('deviceDetails');
  };

  const handleAddDevice = (device: Omit<Device, 'id'>) => {
    const newDevice: Device = {
      ...device,
      id: Date.now().toString(),
    };
    setDevices([...devices, newDevice]);
  };

  const handleDeleteDevice = (deviceId: string) => {
    setDevices(devices.filter(d => d.id !== deviceId));
    if (selectedDeviceId === deviceId) {
      setSelectedDeviceId(null);
      setCurrentScreen('deviceList');
    }
  };

  const handleAddExcludedSound = (sound: Omit<ExcludedSound, 'id'>) => {
    const newSound: ExcludedSound = {
      ...sound,
      id: Date.now().toString(),
    };
    setExcludedSounds([...excludedSounds, newSound]);
  };

  const handleDeleteExcludedSound = (soundId: string) => {
    setExcludedSounds(excludedSounds.filter(s => s.id !== soundId));
  };

  const handleAddSpecificSound = (sound: Omit<SpecificSound, 'id'>) => {
    const newSound: SpecificSound = {
      ...sound,
      id: Date.now().toString(),
    };
    setSpecificSounds([...specificSounds, newSound]);
  };

  const handleDeleteSpecificSound = (soundId: string) => {
    setSpecificSounds(specificSounds.filter(s => s.id !== soundId));
  };

  const selectedDevice = devices.find(d => d.id === selectedDeviceId);

  return (
    <div className="min-h-screen bg-gray-50">
      {currentScreen === 'deviceList' && (
        <DeviceListScreen
          devices={devices}
          selectedDeviceId={selectedDeviceId}
          onSelectDevice={handleSelectDevice}
          onAddDevice={handleAddDevice}
          onDeleteDevice={handleDeleteDevice}
        />
      )}
      
      {currentScreen === 'deviceDetails' && selectedDevice && (
        <DeviceDetailsScreen
          device={selectedDevice}
          onBack={() => setCurrentScreen('deviceList')}
          onNavigateToExcludingSounds={() => setCurrentScreen('excludingSounds')}
          onNavigateToSpecificSounds={() => setCurrentScreen('specificSounds')}
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
