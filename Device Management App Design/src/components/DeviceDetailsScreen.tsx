import { ArrowLeft, Volume2, Music, MessageSquare, Zap, Activity, Thermometer, Cpu, Wifi, VolumeX, Bell } from 'lucide-react';
import { useState, useEffect } from 'react';
import { Device, AudioEvent } from '../App';
import { SoundIntensityGraph } from './SoundIntensityGraph';

type Props = {
  device: Device;
  onBack: () => void;
  onNavigateToExcludingSounds: () => void;
  onNavigateToSpecificSounds: () => void;
};

export function DeviceDetailsScreen({ 
  device, 
  onBack, 
  onNavigateToExcludingSounds,
  onNavigateToSpecificSounds 
}: Props) {
  const [currentEvent, setCurrentEvent] = useState<AudioEvent>({
    id: '1',
    type: 'voice',
    timestamp: new Date(),
    intensity: 65,
    description: 'Conversation detected',
  });

  const [recentEvents, setRecentEvents] = useState<AudioEvent[]>([
    {
      id: '10',
      type: 'music',
      timestamp: new Date(Date.now() - 1000 * 30),
      intensity: 45,
      description: 'Background music',
    },
    {
      id: '9',
      type: 'voice',
      timestamp: new Date(Date.now() - 1000 * 120),
      intensity: 72,
      description: 'Voice activity',
    },
    {
      id: '8',
      type: 'noise',
      timestamp: new Date(Date.now() - 1000 * 240),
      intensity: 38,
      description: 'Movement sounds',
    },
    {
      id: '7',
      type: 'alarm',
      timestamp: new Date(Date.now() - 1000 * 360),
      intensity: 85,
      description: 'Alert tone detected',
    },
    {
      id: '6',
      type: 'music',
      timestamp: new Date(Date.now() - 1000 * 480),
      intensity: 52,
      description: 'Music playing',
    },
    {
      id: '5',
      type: 'voice',
      timestamp: new Date(Date.now() - 1000 * 600),
      intensity: 68,
      description: 'Conversation',
    },
    {
      id: '4',
      type: 'noise',
      timestamp: new Date(Date.now() - 1000 * 720),
      intensity: 42,
      description: 'Environmental noise',
    },
    {
      id: '3',
      type: 'unknown',
      timestamp: new Date(Date.now() - 1000 * 840),
      intensity: 25,
      description: 'Unclassified sound',
    },
    {
      id: '2',
      type: 'voice',
      timestamp: new Date(Date.now() - 1000 * 960),
      intensity: 78,
      description: 'Voice detected',
    },
    {
      id: '1',
      type: 'music',
      timestamp: new Date(Date.now() - 1000 * 1080),
      intensity: 48,
      description: 'Background music',
    },
  ]);

  useEffect(() => {
    // Simulate real-time updates
    const interval = setInterval(() => {
      const types: AudioEvent['type'][] = ['voice', 'noise', 'music', 'alarm', 'unknown'];
      const descriptions = [
        'Voice activity',
        'Conversation detected',
        'Background music',
        'Movement sounds',
        'Alert tone',
        'Environmental noise',
        'Unknown sound',
      ];
      
      const randomType = types[Math.floor(Math.random() * types.length)];
      const randomIntensity = Math.floor(Math.random() * 60) + 30;
      const randomDescription = descriptions[Math.floor(Math.random() * descriptions.length)];

      const newEvent: AudioEvent = {
        id: Date.now().toString(),
        type: randomType,
        timestamp: new Date(),
        intensity: randomIntensity,
        description: randomDescription,
      };

      setCurrentEvent(newEvent);
      setRecentEvents(prev => [newEvent, ...prev.slice(0, 9)]);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const eventIcons = {
    voice: MessageSquare,
    music: Music,
    noise: Volume2,
    alarm: Bell,
    unknown: Activity,
  };

  const eventColors = {
    voice: 'text-blue-600 bg-blue-50',
    music: 'text-purple-600 bg-purple-50',
    noise: 'text-gray-600 bg-gray-50',
    alarm: 'text-red-600 bg-red-50',
    unknown: 'text-orange-600 bg-orange-50',
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const EventIcon = eventIcons[currentEvent.type];

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 py-4">
          <div className="flex items-center gap-3 mb-4">
            <button
              onClick={onBack}
              className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-gray-700" />
            </button>
            <div className="flex-1">
              <h1 className="text-gray-900">{device.name}</h1>
              <p className="text-gray-600 text-sm">{device.ipAddress}</p>
            </div>
            <div className={`w-3 h-3 rounded-full ${
              device.status === 'online' ? 'bg-green-500' : 
              device.status === 'error' ? 'bg-red-500' : 
              'bg-gray-400'
            }`} />
          </div>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 py-6">
        {/* Current Recognition */}
        <div className="bg-white rounded-2xl p-6 shadow-sm mb-4">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-5 h-5 text-gray-700" />
            <h2 className="text-gray-900">Current Recognition</h2>
            <div className="ml-auto w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          </div>

          <div className="flex items-center gap-4 mb-6">
            <div className={`w-16 h-16 rounded-2xl flex items-center justify-center ${eventColors[currentEvent.type]}`}>
              <EventIcon className={`w-8 h-8 ${eventColors[currentEvent.type].split(' ')[0]}`} />
            </div>
            <div className="flex-1">
              <h3 className="text-gray-900 mb-1">{currentEvent.description}</h3>
              <p className="text-gray-600 text-sm">{formatTime(currentEvent.timestamp)}</p>
            </div>
          </div>

          {/* Sound Intensity */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-700 text-sm">Sound Intensity</span>
              <span className="text-gray-900">{currentEvent.intensity} dB</span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 transition-all duration-500"
                style={{ width: `${currentEvent.intensity}%` }}
              />
            </div>
          </div>

          <SoundIntensityGraph />
        </div>

        {/* Recent Events */}
        <div className="bg-white rounded-2xl p-6 shadow-sm mb-4">
          <h2 className="text-gray-900 mb-4">Recent Events</h2>
          <div className="space-y-2">
            {recentEvents.map((event) => {
              const Icon = eventIcons[event.type];
              return (
                <div key={event.id} className="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${eventColors[event.type]}`}>
                    <Icon className={`w-5 h-5 ${eventColors[event.type].split(' ')[0]}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-gray-900 text-sm truncate">{event.description}</p>
                    <p className="text-gray-500 text-xs">{formatTime(event.timestamp)}</p>
                  </div>
                  <div className="text-gray-600 text-sm">{event.intensity} dB</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Device Health */}
        <div className="bg-white rounded-2xl p-6 shadow-sm mb-4">
          <h2 className="text-gray-900 mb-4">Device Health</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-orange-50 rounded-xl">
              <div className="flex items-center gap-2 mb-2">
                <Thermometer className="w-5 h-5 text-orange-600" />
                <span className="text-orange-900 text-sm">Temperature</span>
              </div>
              <p className="text-orange-900">{device.temperature || 'N/A'}°C</p>
            </div>
            <div className="p-4 bg-blue-50 rounded-xl">
              <div className="flex items-center gap-2 mb-2">
                <Cpu className="w-5 h-5 text-blue-600" />
                <span className="text-blue-900 text-sm">CPU Load</span>
              </div>
              <p className="text-blue-900">{device.cpuLoad || 'N/A'}%</p>
            </div>
            <div className="p-4 bg-green-50 rounded-xl col-span-2">
              <div className="flex items-center gap-2 mb-2">
                <Wifi className="w-5 h-5 text-green-600" />
                <span className="text-green-900 text-sm">Connectivity</span>
              </div>
              <p className="text-green-900">Connected · {device.ipAddress}</p>
            </div>
          </div>
        </div>

        {/* Navigation Buttons */}
        <div className="space-y-3 pb-6">
          <button
            onClick={onNavigateToExcludingSounds}
            className="w-full bg-white border-2 border-gray-200 text-gray-900 py-4 px-6 rounded-xl flex items-center justify-between active:bg-gray-50 transition-colors shadow-sm"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                <VolumeX className="w-5 h-5 text-purple-600" />
              </div>
              <div className="text-left">
                <p className="text-gray-900">Excluding Sounds</p>
                <p className="text-gray-600 text-sm">Manage ignored sounds</p>
              </div>
            </div>
            <div className="text-gray-400">›</div>
          </button>

          <button
            onClick={onNavigateToSpecificSounds}
            className="w-full bg-white border-2 border-gray-200 text-gray-900 py-4 px-6 rounded-xl flex items-center justify-between active:bg-gray-50 transition-colors shadow-sm"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-red-100 rounded-xl flex items-center justify-center">
                <Zap className="w-5 h-5 text-red-600" />
              </div>
              <div className="text-left">
                <p className="text-gray-900">Specific Sounds</p>
                <p className="text-gray-600 text-sm">Track important sounds</p>
              </div>
            </div>
            <div className="text-gray-400">›</div>
          </button>
        </div>
      </div>
    </div>
  );
}
