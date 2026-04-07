import { useState, useEffect } from 'react';
import { X, Bell } from 'lucide-react';
import { apiClient } from '../api/client';

interface Notification {
  id: string;
  soundType: string;
  confidence: number;
  deviceId: string;
  deviceName: string;
  timestamp: string;
  isRead: boolean;
}

interface Props {
  onSoundDetected: (data: any) => void;
}

export function ImprovedNotificationManagerSimple({ onSoundDetected }: Props) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);

  useEffect(() => {
    const handleSoundDetected = (event: any) => {
      const data = event.detail;
      console.log('🔔 Notification received:', data);
      const { sound_type, confidence, device_id, timestamp, should_notify } = data;
      
      if (should_notify === false) return;
      
      // Создаем уникальный ID на основе timestamp и device_id для предотвращения дубликатов
      const uniqueId = `${device_id}-${sound_type}-${Math.floor(new Date(timestamp).getTime() / 1000)}`;
      
      const notification: Notification = {
        id: uniqueId,
        soundType: sound_type || 'Unknown',
        confidence: confidence || 0,
        deviceId: device_id || 'unknown',
        deviceName: `Device ${device_id ? device_id.slice(-4) : 'Unknown'}`,
        timestamp,
        isRead: false,
      };
      
      setNotifications(prev => {
        // Проверяем на дубликаты по ID
        if (prev.some(n => n.id === uniqueId)) {
          return prev;
        }
        return [notification, ...prev.slice(0, 49)];
      });
    };

    window.addEventListener('soundDetected', handleSoundDetected);
    return () => window.removeEventListener('soundDetected', handleSoundDetected);
  }, []);

  const unreadCount = notifications.filter(n => !n.isRead).length;

  const getSoundIcon = (soundType: string): string => {
    const lowerSound = soundType?.toLowerCase() || '';
    if (lowerSound.includes('speech')) return '🗣️';
    if (lowerSound.includes('typing')) return '⌨️';
    if (lowerSound.includes('silence')) return '🤫';
    return '🔊';
  };

  return (
    <>
      {/* Кнопка уведомлений */}
      <button
        onClick={() => setShowNotifications(true)}
        className="fixed top-6 right-6 p-3 bg-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105 active:scale-95 z-40"
      >
        <Bell className="w-5 h-5 text-gray-700" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center animate-pulse">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Панель уведомлений */}
      {showNotifications && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white w-full max-w-md h-[80vh] rounded-2xl shadow-2xl flex flex-col md:w-96">
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                  <Bell className="w-5 h-5 text-blue-600" />
                  Уведомления
                </h2>
                <button
                  onClick={() => setShowNotifications(false)}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="text-center py-8">
                  <Bell className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">Нет уведомлений</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-200">
                  {notifications.map((notification) => (
                    <div key={notification.id} className="p-4 hover:bg-gray-50">
                      <div className="flex items-start gap-3">
                        <span className="text-xl">{getSoundIcon(notification.soundType)}</span>
                        <div className="flex-1">
                          <h4 className="text-sm font-medium text-gray-900">{notification.soundType}</h4>
                          <p className="text-xs text-gray-600 mt-1">
                            {notification.deviceName} • {(notification.confidence * 100).toFixed(1)}%
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(notification.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
