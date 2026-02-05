import { useState, useEffect } from 'react';
import { X, AlertTriangle, Bell, CheckCircle, AlertCircle } from 'lucide-react';
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

export function ImprovedNotificationManager({ onSoundDetected }: Props) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [notificationSettings, setNotificationSettings] = useState<{
    notification_sounds: string[];
    excluded_sounds: string[];
    custom_sounds: {name: string, type: string}[];
  }>({
    notification_sounds: [],
    excluded_sounds: [],
    custom_sounds: []
  });

  // Загружаем настройки уведомлений
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const devices = await apiClient.getDevices();
        if (devices.length > 0) {
          const settings = await apiClient.getNotificationSettings(devices[0].id);
          setNotificationSettings(settings);
        }
      } catch (error) {
        console.error('Error loading notification settings:', error);
      }
    };
    
    loadSettings();
  }, []);

  useEffect(() => {
    const handleSoundDetected = (event: any) => {
      const data = event.detail; // Получаем данные из CustomEvent
      console.log('🔔 Notification received:', data); // Логируем для отладки
      const { sound_type, confidence, device_id, timestamp, should_notify } = data;
      
      // Проверяем нужно ли показывать уведомление
      if (should_notify === false) {
        return; // Не показываем уведомление если звук исключен
      }
      
      // Показываем уведомление
      const notification: Notification = {
        id: `${device_id}-${Date.now()}`,
        soundType: sound_type,
        confidence,
        deviceId: device_id,
        deviceName: `Device ${device_id.slice(-4)}`, // Временно, потом получим настоящее имя
        timestamp,
        isRead: false,
      };
      
      console.log('🔔 Creating notification:', notification); // Логируем уведомление
      
      setNotifications(prev => {
        // Проверяем на дубликаты
        const isDuplicate = prev.some(n => 
          n.soundType === sound_type && 
          Math.abs(new Date(n.timestamp).getTime() - new Date(timestamp).getTime()) < 2000
        );
        
        if (!isDuplicate) {
          return [notification, ...prev.slice(0, 99)]; // Максимум 100 уведомлений
        }
        return prev;
      });
      
      // Автоматически скрываем всплывающее уведомление через 4 секунды
      setTimeout(() => {
        setNotifications(prev => prev.map(n => 
          n.id === notification.id ? { ...n, isRead: true } : n
        ));
      }, 4000);
    };

    // Используем addEventListener для CustomEvent
    window.addEventListener('soundDetected', handleSoundDetected);
    
    return () => {
      window.removeEventListener('soundDetected', handleSoundDetected);
    };
  }, [onSoundDetected]);

  const unreadCount = notifications.filter(n => !n.isRead).length;

  const markAsRead = (id: string) => {
    setNotifications(prev => prev.map(n => 
      n.id === id ? { ...n, isRead: true } : n
    ));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const getSoundIcon = (soundType: string): string => {
    const iconMap: { [key: string]: string } = {
      'baby cry': '👶',
      'fire': '🔥',
      'fire alarm': '🚨',
      'siren': '🚓',
      'glass breaking': '💔',
      'smoke alarm': '💨',
      'silence': '🤫',
      'speech': '🗣️',
      'typing': '⌨️',
    };
    
    const lowerSound = soundType.toLowerCase();
    for (const [key, icon] of Object.entries(iconMap)) {
      if (lowerSound.includes(key)) {
        return icon;
      }
    }
    return '🔊';
  };

  // Popup уведомление
  const PopupNotification = () => {
    const latestUnread = notifications.find(n => !n.isRead);
    
    if (!latestUnread) return null;
    
    return (
      <div className="fixed top-24 right-6 z-50 animate-in slide-in-from-right fade-in duration-300">
        <div className="bg-white rounded-lg shadow-lg border-l-4 border-blue-500 p-4 min-w-80 max-w-96">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0">
              <span className="text-2xl">{getSoundIcon(latestUnread.soundType)}</span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <h4 className="text-sm font-semibold text-gray-900 truncate">
                  {latestUnread.soundType}
                </h4>
                <button
                  onClick={() => markAsRead(latestUnread.id)}
                  className="flex-shrink-0 p-1 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <X className="w-4 h-4 text-gray-400" />
                </button>
              </div>
              <p className="text-xs text-gray-600 mb-1">
                {latestUnread.deviceName} • {(latestUnread.confidence * 100).toFixed(1)}%
              </p>
              <p className="text-xs text-gray-500">
                {new Date(latestUnread.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Панель уведомлений
  const NotificationPanel = () => {
    if (!showNotifications) return null;
    
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="absolute inset-0 bg-black/50" onClick={() => setShowNotifications(false)} />
        <div className="relative w-full max-w-md bg-white rounded-lg shadow-xl overflow-hidden animate-in slide-in-from-bottom fade-in duration-200 max-h-[80vh] flex flex-col">
          <div className="p-4 border-b bg-gray-50 flex-shrink-0">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Уведомления</h3>
              <button
                onClick={() => setShowNotifications(false)}
                className="p-2 hover:bg-gray-200 rounded-full transition-colors"
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
                  <div
                    key={notification.id}
                    className={`p-4 hover:bg-gray-50 transition-colors cursor-pointer ${
                      !notification.isRead ? 'bg-blue-50' : ''
                    }`}
                    onClick={() => markAsRead(notification.id)}
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-xl flex-shrink-0">
                        {getSoundIcon(notification.soundType)}
                      </span>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-medium text-gray-900 truncate">
                          {notification.soundType}
                        </h4>
                        <p className="text-xs text-gray-600 mt-1">
                          {notification.deviceName} • {(notification.confidence * 100).toFixed(1)}%
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {new Date(notification.timestamp).toLocaleString()}
                        </p>
                      </div>
                      {!notification.isRead && (
                        <div className="flex-shrink-0 w-2 h-2 bg-blue-600 rounded-full mt-2" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          {notifications.length > 0 && (
            <div className="p-4 border-t bg-gray-50 flex-shrink-0">
              <button
                onClick={clearAll}
                className="w-full py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              >
                Очистить все уведомления
              </button>
            </div>
          )}
        </div>
      </div>
    );
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

      {/* Popup уведомление */}
      <PopupNotification />
      
      {/* Панель уведомлений */}
      <NotificationPanel />
    </>
  );
}
