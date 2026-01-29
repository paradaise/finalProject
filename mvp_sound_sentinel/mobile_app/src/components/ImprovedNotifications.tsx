import { useState, useEffect } from 'react';
import { X, AlertTriangle, Bell, CheckCircle, AlertCircle } from 'lucide-react';
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
  isRead: boolean;
}

interface Props {
  customSounds: { [key: string]: any[] };
  onSoundDetected: (data: any) => void;
}

export function ImprovedNotificationManager({ customSounds, onSoundDetected }: Props) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);

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
          isRead: false,
        };
        
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
      }
      
      onSoundDetected(data);
    };
    
    window.addEventListener('soundDetected', (event: any) => {
      handleSoundDetected(event.detail);
    });
    
    return () => {
      window.removeEventListener('soundDetected', handleSoundDetected);
    };
  }, [customSounds, onSoundDetected]);

  const unreadCount = notifications.filter(n => !n.isRead).length;

  return (
    <>
      {/* Всплывающие уведомления */}
      <div className="fixed top-4 right-4 sm:top-6 sm:right-6 z-50 space-y-2 max-w-xs sm:max-w-sm">
        {notifications.filter(n => !n.isRead).slice(0, 3).map((notification) => (
          <PopupNotification
            key={notification.id}
            notification={notification}
            onClose={() => markAsRead(notification.id)}
          />
        ))}
      </div>

      {/* Кнопка уведомлений */}
      <div className="fixed top-6 right-6 z-40">
        <button
          onClick={() => setShowNotifications(!showNotifications)}
          className="relative p-3 sm:p-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-full shadow-2xl hover:shadow-3xl transform hover:scale-110 transition-all duration-300 group"
        >
          <Bell className="w-5 h-5 sm:w-6 sm:h-6" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 sm:-top-2 sm:-right-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 sm:w-6 sm:h-6 flex items-center justify-center animate-pulse">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </button>
      </div>

      {/* Панель уведомлений */}
      {showNotifications && (
        <NotificationPanel
          notifications={notifications}
          onClose={() => setShowNotifications(false)}
          onMarkAsRead={markAsRead}
          onClearAll={clearAll}
        />
      )}
    </>
  );

  function markAsRead(id: string) {
    setNotifications(prev => prev.map(n => 
      n.id === id ? { ...n, isRead: true } : n
    ));
  }

  function clearAll() {
    setNotifications([]);
  }
}

interface PopupNotificationProps {
  notification: Notification;
  onClose: () => void;
}

function PopupNotification({ notification, onClose }: PopupNotificationProps) {
  const { soundType, confidence, deviceName, timestamp, isCritical, isImportant } = notification;
  
  const bgColor = isCritical 
    ? 'bg-gradient-to-r from-red-50 to-red-100 border-red-300' 
    : isImportant 
    ? 'bg-gradient-to-r from-yellow-50 to-yellow-100 border-yellow-300' 
    : 'bg-gradient-to-r from-blue-50 to-blue-100 border-blue-300';
    
  const iconColor = isCritical 
    ? 'text-red-600' 
    : isImportant 
    ? 'text-yellow-600' 
    : 'text-blue-600';
    
  const soundIcon = getSoundIcon(soundType);

  return (
    <div className={`${bgColor} rounded-xl shadow-2xl border-2 p-3 sm:p-4 transform transition-all duration-500 animate-in slide-in-from-right fade-in`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-2 sm:gap-3 flex-1">
          {/* Анимированная иконка */}
          <div className={`p-2 sm:p-3 rounded-full ${bgColor} animate-pulse`}>
            <span className="text-2xl sm:text-3xl animate-bounce">{soundIcon}</span>
          </div>
          
          {/* Контент */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 sm:mb-2">
              {isCritical && <AlertTriangle className={`w-4 h-4 sm:w-5 sm:h-5 ${iconColor} animate-pulse`} />}
              {isImportant && <AlertCircle className={`w-4 h-4 sm:w-5 sm:h-5 ${iconColor} animate-pulse`} />}
              <h4 className="font-bold text-gray-900 text-sm sm:text-lg">
                {isCritical ? '⚠️ Критический звук!' : isImportant ? '🔔 Важный звук!' : '🔊 Звук обнаружен'}
              </h4>
            </div>
            
            <p className="text-gray-800 font-semibold text-sm sm:text-lg truncate">{soundType}</p>
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 mt-1 sm:mt-2">
              <p className="text-xs sm:text-sm text-gray-700 font-medium">
                Уверенность: <span className="text-sm sm:text-lg font-bold">{(confidence * 100).toFixed(1)}%</span>
              </p>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <p className="text-xs text-gray-600 truncate">{deviceName}</p>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {new Date(timestamp).toLocaleString('ru-RU')}
            </p>
          </div>
        </div>
        
        {/* Кнопка закрытия */}
        <button
          onClick={onClose}
          className="p-1.5 sm:p-2 hover:bg-white/50 rounded-full transition-all duration-200 transform hover:scale-110 active:scale-95 group"
        >
          <X className="w-3 h-3 sm:w-4 sm:h-4 text-gray-600 transition-transform group-hover:rotate-90" />
        </button>
      </div>
      
      {/* Прогресс-бар авто-скрытия */}
      <div className="mt-2 sm:mt-3 h-1 bg-gray-200 rounded-full overflow-hidden">
        <div className="h-full bg-gradient-to-r from-blue-500 to-purple-500 animate-pulse" 
             style={{ 
               animation: 'shrink 4s linear forwards',
               width: '100%'
             }}>
        </div>
      </div>
    </div>
  );
}

interface NotificationPanelProps {
  notifications: Notification[];
  onClose: () => void;
  onMarkAsRead: (id: string) => void;
  onClearAll: () => void;
}

function NotificationPanel({ notifications, onClose, onMarkAsRead, onClearAll }: NotificationPanelProps) {
  const unreadCount = notifications.filter(n => !n.isRead).length;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-2 sm:p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg sm:max-w-2xl max-h-[85vh] sm:max-h-[80vh] flex flex-col animate-in fade-in zoom-in duration-300">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-4 sm:p-6 rounded-t-2xl">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold flex items-center gap-2">
                <Bell className="w-5 h-5 sm:w-6 sm:h-6" />
                Уведомления
              </h2>
              <p className="text-purple-100 mt-1 text-sm sm:text-base">
                {unreadCount} непрочитанных из {notifications.length}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {notifications.length > 0 && (
                <button
                  onClick={onClearAll}
                  className="px-3 py-1.5 sm:px-4 sm:py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors text-xs sm:text-sm font-medium hover:scale-105 active:scale-95"
                >
                  Очистить все
                </button>
              )}
              <button
                onClick={onClose}
                className="p-2 hover:bg-white/20 rounded-full transition-colors hover:scale-110 active:scale-95"
              >
                <X className="w-4 h-4 sm:w-5 sm:h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Notifications List */}
        <div className="flex-1 overflow-y-auto p-3 sm:p-4">
          {notifications.length === 0 ? (
            <div className="text-center py-8 sm:py-12">
              <CheckCircle className="w-12 h-12 sm:w-16 sm:h-16 text-gray-300 mx-auto mb-3 sm:mb-4" />
              <p className="text-gray-500 text-base sm:text-lg">Нет уведомлений</p>
              <p className="text-gray-400 text-xs sm:text-sm mt-2">Здесь появятся уведомления о важных звуках</p>
            </div>
          ) : (
            <div className="space-y-2 sm:space-y-3">
              {notifications.map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  onMarkAsRead={onMarkAsRead}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface NotificationItemProps {
  notification: Notification;
  onMarkAsRead: (id: string) => void;
}

function NotificationItem({ notification, onMarkAsRead }: NotificationItemProps) {
  const { soundType, confidence, deviceName, timestamp, isCritical, isImportant, isRead } = notification;
  
  const bgColor = isCritical 
    ? 'border-red-200 bg-red-50' 
    : isImportant 
    ? 'border-yellow-200 bg-yellow-50' 
    : 'border-blue-200 bg-blue-50';
    
  const soundIcon = getSoundIcon(soundType);

  return (
    <div className={`border-2 rounded-xl p-3 sm:p-4 transition-all duration-200 hover:shadow-md ${bgColor} ${!isRead ? 'shadow-md' : 'opacity-75'} hover:scale-[1.02] active:scale-[0.98]`}>
      <div className="flex items-start gap-2 sm:gap-3">
        <div className="text-xl sm:text-2xl flex-shrink-0">{soundIcon}</div>
        <div className="flex-1 min-w-0">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <h4 className="font-semibold text-gray-900 text-sm sm:text-base truncate">{soundType}</h4>
            {!isRead && (
              <span className="px-2 py-1 bg-blue-100 text-blue-600 text-xs rounded-full font-medium self-start sm:self-auto">
                Новое
              </span>
            )}
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 mt-1 text-xs sm:text-sm text-gray-600">
            <span>Уверенность: {(confidence * 100).toFixed(1)}%</span>
            <span className="truncate">{deviceName}</span>
          </div>
          <p className="text-xs text-gray-500 mt-1 sm:mt-2">
            {new Date(timestamp).toLocaleString('ru-RU')}
          </p>
        </div>
        {!isRead && (
          <button
            onClick={() => onMarkAsRead(notification.id)}
            className="p-1.5 sm:p-2 hover:bg-gray-100 rounded-full transition-all duration-200 hover:scale-110 active:scale-95 group flex-shrink-0"
          >
            <CheckCircle className="w-3 h-3 sm:w-4 sm:h-4 text-gray-400 transition-transform group-hover:scale-110 group-hover:text-green-500" />
          </button>
        )}
      </div>
    </div>
  );
}

// Добавляем CSS анимации
const style = document.createElement('style');
style.textContent = `
  @keyframes shrink {
    from { width: 100%; }
    to { width: 0%; }
  }
  
  @keyframes bell {
    0%, 100% { transform: rotate(0deg); }
    25% { transform: rotate(10deg); }
    75% { transform: rotate(-10deg); }
  }
  
  .animate-bell {
    animation: bell 0.5s ease-in-out;
  }
  
  /* Hover анимации для десктопа */
  @media (hover: hover) and (pointer: fine) {
    .group:hover .group-hover\\:animate-bell {
      animation: bell 0.5s ease-in-out infinite;
    }
    
    .group:hover .group-hover\\:rotate-90 {
      transform: rotate(90deg);
    }
    
    .group:hover .group-hover\\:rotate-45 {
      transform: rotate(45deg);
    }
    
    .group:hover .group-hover\\:-translate-x-1 {
      transform: translateX(-4px);
    }
    
    .group:hover .group-hover\\:scale-110 {
      transform: scale(1.1);
    }
  }
  
  /* Touch анимации для мобильных */
  @media (hover: none) and (pointer: coarse) {
    .group:active .group-hover\\:animate-bell {
      animation: bell 0.3s ease-in-out;
    }
    
    .group:active .group-hover\\:rotate-90 {
      transform: rotate(90deg);
    }
    
    .group:active .group-hover\\:rotate-45 {
      transform: rotate(45deg);
    }
    
    .group:active .group-hover\\:-translate-x-1 {
      transform: translateX(-4px);
    }
    
    .group:active .group-hover\\:scale-110 {
      transform: scale(1.1);
    }
    
    /* Анимации при нажатии на кнопки */
    button:active {
      transform: scale(0.95) !important;
    }
    
    button:hover {
      transform: scale(1.05) !important;
    }
  }
  
  /* Общие анимации */
  .transition-transform {
    transition: transform 0.2s ease-in-out;
  }
  
  .hover\\:scale-110:hover {
    transform: scale(1.1);
  }
  
  .active\\:scale-95:active {
    transform: scale(0.95);
  }
  
  .hover\\:scale-105:hover {
    transform: scale(1.05);
  }
  
  .hover\\:shadow-xl:hover {
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  }
`;
document.head.appendChild(style);
