import { useState, useEffect } from 'react';
import { Bell, Trash2 } from 'lucide-react';
import { isCriticalSound, isImportantSound, getSoundIcon, isExcludedSound } from '../data/criticalSounds';

interface Notification {
  id: string;
  soundType: string;
  confidence: number;
  deviceId: string;
  deviceName: string;
  timestamp: string;
  isCritical: boolean;
  isImportant: boolean;
  isCustom: boolean;
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
      
      // Проверяем на исключенные звуки
      if (isExcludedSound(sound_type)) {
        onSoundDetected(data);
        return;
      }
      
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
          isCustom: isCustomImportant,
        };
        
        setNotifications(prev => {
          // Проверяем на дубликаты
          const isDuplicate = prev.some(n => 
            n.soundType === sound_type && 
            Math.abs(new Date(n.timestamp).getTime() - new Date(timestamp).getTime()) < 2000
          );
          
          if (!isDuplicate) {
            return [notification, ...prev.slice(0, 4)]; // Максимум 5 уведомлений
          }
          return prev;
        });
        
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
    <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 max-w-sm sm:max-w-md lg:max-w-lg">
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
        <div className="space-y-2 max-h-96 overflow-y-auto">
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
  const { soundType, confidence, deviceName, timestamp, isCritical, isImportant, isCustom } = notification;
  
  const soundIcon = getSoundIcon(soundType);
  
  // Определяем цветовую схему
  const borderColor = isCritical 
    ? 'border-red-500 bg-red-50' 
    : isImportant 
    ? 'border-yellow-500 bg-yellow-50' 
    : 'border-green-500 bg-green-50';
    
  const textColor = isCritical 
    ? 'text-red-700' 
    : isImportant 
    ? 'text-yellow-700' 
    : 'text-green-700';

  return (
    <div className={`border-l-4 ${borderColor} p-3 transition-all duration-200 hover:shadow-sm`}>
      <div className="flex items-center justify-between">
        
        {/* Левая часть: иконка + основная информация */}
        <div className="flex items-center gap-3 flex-1">
          {/* Компактная иконка */}
          <div className={`w-8 h-8 rounded-full bg-white flex items-center justify-center flex-shrink-0 shadow-sm`}>
            <span className="text-lg">{soundIcon}</span>
          </div>
          
          {/* Текстовая информация */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-medium text-gray-900 text-sm truncate">
                {soundType}
              </h3>
              <span className={`text-xs font-medium ${textColor}`}>
                {isCritical ? '!' : isImportant ? '‼' : ''}
              </span>
            </div>
            
            <div className="text-xs text-gray-500">
              {deviceName} • {new Date(timestamp).toLocaleTimeString()} • {(confidence * 100).toFixed(1)}%
            </div>
          </div>
        </div>
        
        {/* Правая часть: тип + удаление */}
        <div className="flex items-center gap-2 ml-3">
          {/* Тип источника */}
          <span className={`text-xs px-1.5 py-0.5 rounded ${
            isCustom 
              ? 'bg-purple-100 text-purple-700' 
              : 'bg-blue-100 text-blue-700'
          }`}>
            {isCustom ? 'П' : 'Y'}
          </span>
          
          {/* Кнопка удаления */}
          <button
            onClick={onClose}
            disabled={isCustom}
            className={`p-1 rounded transition-colors ${
              isCustom 
                ? 'text-gray-300 cursor-not-allowed' 
                : 'text-gray-400 hover:text-gray-600'
            }`}
            title={isCustom ? 'Удалить из настроек' : 'Удалить уведомление'}
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
        
      </div>
    </div>
  );
}
