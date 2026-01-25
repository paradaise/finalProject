import { useState, useEffect } from 'react';
import { X, AlertTriangle, Bell } from 'lucide-react';
import { isCriticalSound, isImportantSound, getSoundIcon } from '../data/criticalSounds';

interface Notification {
  id: string;
  soundType: string;
  confidence: number;
  deviceId: string;
  deviceName: string;
  timestamp: string;
  isCritical: boolean;
  isImportant: boolean;
}

interface Props {
  customSounds: { [key: string]: any[] };
  onSoundDetected: (data: any) => void;
}

export function NotificationManager({ customSounds, onSoundDetected }: Props) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const handleSoundDetected = (data: any) => {
      const { sound_type, confidence, device_id, timestamp } = data;
      
      // Проверяем критичность и важность
      const isCritical = isCriticalSound(sound_type);
      const isImportant = isImportantSound(sound_type);
      
      // Проверяем пользовательские важные звуки
      const deviceImportantSounds = customSounds[device_id] || [];
      const isCustomImportant = deviceImportantSounds.some(
        (sound: any) => sound.sound_type === 'important' && 
        sound.name.toLowerCase().includes(sound_type.toLowerCase())
      );
      
      // Показываем уведомление только для критических, важных или пользовательских звуков
      if (isCritical || isImportant || isCustomImportant) {
        const notification: Notification = {
          id: `${device_id}-${Date.now()}`,
          soundType: sound_type,
          confidence,
          deviceId: device_id,
          deviceName: `Устройство ${device_id.substring(0, 8)}`,
          timestamp,
          isCritical,
          isImportant: isImportant || isCustomImportant,
        };
        
        setNotifications(prev => [notification, ...prev.slice(0, 4)]); // Максимум 5 уведомлений
        
        // Автоматически скрываем через 5 секунд
        setTimeout(() => {
          setNotifications(prev => prev.filter(n => n.id !== notification.id));
        }, 5000);
      }
      
      onSoundDetected(data);
    };
    
    // Подписываемся на события звуков
    window.addEventListener('soundDetected', (event: any) => {
      handleSoundDetected(event.detail);
    });
    
    return () => {
      window.removeEventListener('soundDetected', handleSoundDetected);
    };
  }, [customSounds, onSoundDetected]);

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  if (notifications.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 max-w-sm">
      {/* Кнопка сворачивания/разворачивания */}
      <div className="flex justify-end mb-2">
        <button
          onClick={() => setIsVisible(!isVisible)}
          className="p-2 bg-white rounded-full shadow-lg hover:shadow-xl transition-shadow"
        >
          <Bell className="w-5 h-5 text-gray-600" />
          {notifications.length > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
              {notifications.length}
            </span>
          )}
        </button>
      </div>

      {/* Уведомления */}
      {isVisible && (
        <div className="space-y-2">
          {notifications.map((notification) => (
            <NotificationItem
              key={notification.id}
              notification={notification}
              onClose={() => removeNotification(notification.id)}
            />
          ))}
          
          {/* Кнопка очистки всех */}
          {notifications.length > 1 && (
            <button
              onClick={clearAll}
              className="w-full p-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-sm text-gray-600"
            >
              Очистить все уведомления
            </button>
          )}
        </div>
      )}
    </div>
  );
}

interface NotificationItemProps {
  notification: Notification;
  onClose: () => void;
}

function NotificationItem({ notification, onClose }: NotificationItemProps) {
  const { soundType, confidence, deviceName, timestamp, isCritical, isImportant } = notification;
  
  const bgColor = isCritical 
    ? 'bg-red-50 border-red-200' 
    : isImportant 
    ? 'bg-yellow-50 border-yellow-200' 
    : 'bg-blue-50 border-blue-200';
    
  const iconColor = isCritical 
    ? 'text-red-600' 
    : isImportant 
    ? 'text-yellow-600' 
    : 'text-blue-600';
    
  const soundIcon = getSoundIcon(soundType);

  return (
    <div className={`bg-white rounded-lg shadow-lg border-2 ${bgColor} p-4 transform transition-all duration-300 animate-in slide-in-from-right`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1">
          {/* Иконка */}
          <div className={`p-2 rounded-full ${bgColor}`}>
            <span className="text-2xl">{soundIcon}</span>
          </div>
          
          {/* Контент */}
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              {isCritical && <AlertTriangle className={`w-4 h-4 ${iconColor}`} />}
              <h4 className="font-semibold text-gray-900">
                {isCritical ? 'Критический звук!' : isImportant ? 'Важный звук!' : 'Звук обнаружен'}
              </h4>
            </div>
            
            <p className="text-gray-800 font-medium">{soundType}</p>
            <p className="text-sm text-gray-600">
              Уверенность: {(confidence * 100).toFixed(1)}%
            </p>
            <p className="text-xs text-gray-500">
              {deviceName} • {new Date(timestamp).toLocaleTimeString()}
            </p>
          </div>
        </div>
        
        {/* Кнопка закрытия */}
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-100 rounded-full transition-colors"
        >
          <X className="w-4 h-4 text-gray-400" />
        </button>
      </div>
    </div>
  );
}
