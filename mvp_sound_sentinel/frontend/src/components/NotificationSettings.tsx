import { useState, useEffect } from 'react';
import { Bell, Filter, Plus, Search, Settings, Trash2, X } from 'lucide-react';
import { apiClient } from '../api/client';

interface NotificationSound {
  name: string;
  type: 'notification' | 'excluded' | 'none';
  icon: string;
  id: string;
  isCustom?: boolean;
}

interface Props {
  onBack: () => void;
}

export function NotificationSettings({ onBack }: Props) {
  const [allSounds, setAllSounds] = useState<string[]>([]);
  const [notificationSounds, setNotificationSounds] = useState<NotificationSound[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState<'all' | 'notification' | 'excluded' | 'none'>('all');
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [customSound, setCustomSound] = useState('');
  const [showYamnetModal, setShowYamnetModal] = useState(false);
  const [yamnetSearch, setYamnetSearch] = useState('');
  const [currentDeviceId, setCurrentDeviceId] = useState<string>('');

  // Загрузка всех звуков YAMNet
  useEffect(() => {
    // Получаем ID первого устройства (для MVP)
    const loadDeviceId = async () => {
      try {
        const devices = await apiClient.getDevices();
        if (devices.length > 0) {
          setCurrentDeviceId(devices[0].id);
          await loadYamnetSounds();
          await loadNotificationSettings(devices[0].id);
        }
      } catch (error) {
        console.error('Error loading device ID:', error);
      }
    };
    
    loadDeviceId();
  }, []);

  const loadYamnetSounds = async () => {
    try {
      const data = await apiClient.getYamnetSounds();
      setAllSounds(data.sounds);
    } catch (error) {
      console.error('Error loading YAMNet sounds:', error);
    }
  };

  const loadNotificationSettings = async (deviceId: string) => {
    try {
      // Загружаем настройки уведомлений из БД
      const settings = await apiClient.getNotificationSettings(deviceId);
      
      const sounds: NotificationSound[] = [];
      const processedSounds = new Set<string>(); // Для отслеживания уникальных звуков
      
      // Добавляем важные звуки
      settings.notification_sounds.forEach((sound) => {
        if (!processedSounds.has(sound.name)) {
          sounds.push({
            name: sound.name,
            type: 'notification',
            icon: getSoundIcon(sound.name),
            id: sound.id
          });
          processedSounds.add(sound.name);
        }
      });
      
      // Добавляем исключенные звуки
      settings.excluded_sounds.forEach((sound) => {
        if (!processedSounds.has(sound.name)) {
          sounds.push({
            name: sound.name,
            type: 'excluded',
            icon: getSoundIcon(sound.name),
            id: sound.id
          });
          processedSounds.add(sound.name);
        }
      });
      
      // Добавляем пользовательские звуки
      settings.custom_sounds.forEach((customSound: {name: string, type: string}) => {
        if (!processedSounds.has(customSound.name)) {
          // 'specific' = важные звуки (уведомления), 'excluded' = исключенные
          const notificationType = customSound.type === 'specific' ? 'notification' : 'excluded';
          console.log('Custom sound:', { 
            name: customSound.name, 
            originalType: customSound.type, 
            notificationType 
          });
          
          sounds.push({
            name: customSound.name,
            type: notificationType,
            icon: getSoundIcon(customSound.name),
            isCustom: true,
            id: `custom-${customSound.name}` // Временный ID для пользовательских звуков
          });
          processedSounds.add(customSound.name);
        }
      });
      
      setNotificationSounds(sounds);
      setLoading(false);
    } catch (error) {
      console.error('Error loading notification settings:', error);
      setLoading(false);
    }
  };

  const getSoundIcon = (sound: string): string => {
    const iconMap: { [key: string]: string } = {
      'baby cry': '👶',
      'fire': '🔥',
      'fire alarm': '🚨',
      'siren': '🚓',
      'glass breaking': '💔',
      'smoke alarm': '💨',
      'water': '💧',
      'door': '🚪',
      'dog': '🐕',
      'cat': '🐈',
      'car': '🚗',
      'phone': '📱',
      'bell': '🔔',
      'alarm': '⏰',
      'music': '🎵',
      'speech': '🗣️',
      'silence': '🤫',
      'typing': '⌨️',
      'keyboard': '⌨️',
      'mouse': '🖱️',
    };
    
    const lowerSound = sound.toLowerCase();
    for (const [key, icon] of Object.entries(iconMap)) {
      if (lowerSound.includes(key)) {
        return icon;
      }
    }
    return '🔊';
  };

  const filteredSounds = notificationSounds.filter(sound => {
    const matchesSearch = sound.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filter === 'all' || sound.type === filter;
    return matchesSearch && matchesFilter;
  });

  const toggleNotificationType = async (soundName: string) => {
    if (!currentDeviceId) return;
    
    const sound = notificationSounds.find(s => s.name === soundName);
    if (!sound || sound.isCustom) return; // Нельзя изменять пользовательские звуки
    
    try {
      // Просто добавляем в новую категорию, не удаляя из старой
      // База данных обработает дубликаты через UNIQUE constraint
      if (sound.type === 'notification') {
        await apiClient.addExcludedSound(soundName, currentDeviceId);
      } else {
        await apiClient.addNotificationSound(soundName, currentDeviceId);
      }
      
      // Обновляем локальное состояние
      setNotificationSounds(prev => prev.map(s => {
        if (s.name === soundName && !s.isCustom) {
          const types: ('notification' | 'excluded')[] = ['notification', 'excluded'];
          const currentIndex = types.indexOf(s.type as 'notification' | 'excluded');
          const nextIndex = (currentIndex + 1) % types.length;
          return { ...s, type: types[nextIndex] };
        }
        return s;
      }));
    } catch (error) {
      console.error('Error toggling notification type:', error);
      // Если звук уже существует, просто обновляем локальное состояние
      if (error instanceof Error && error.message.includes('already exists')) {
        setNotificationSounds(prev => prev.map(s => {
          if (s.name === soundName && !s.isCustom) {
            const types: ('notification' | 'excluded')[] = ['notification', 'excluded'];
            const currentIndex = types.indexOf(s.type as 'notification' | 'excluded');
            const nextIndex = (currentIndex + 1) % types.length;
            return { ...s, type: types[nextIndex] };
          }
          return s;
        }));
      } else {
        alert('Ошибка изменения типа уведомления');
      }
    }
  };

  const addCustomSound = () => {
    if (customSound.trim() && currentDeviceId) {
      const newSound: NotificationSound = {
        name: customSound.trim(),
        type: 'notification',
        icon: getSoundIcon(customSound.trim()),
        isCustom: true,
        id: `custom-${customSound.trim()}-${Date.now()}` // Временный ID
      };
      setNotificationSounds(prev => [...prev, newSound]);
      setCustomSound('');
      setShowAddModal(false);
    }
  };

  const addYamnetSound = async (soundName: string) => {
    if (!currentDeviceId) return;
    
    try {
      // Добавляем как важный звук по умолчанию
      await apiClient.addNotificationSound(soundName, currentDeviceId);
      
      const newSound: NotificationSound = {
        name: soundName,
        type: 'notification',
        icon: getSoundIcon(soundName),
        id: `yamnet-${soundName}-${Date.now()}` // Временный ID
      };
      setNotificationSounds(prev => [...prev, newSound]);
      setShowYamnetModal(false);
      setYamnetSearch('');
    } catch (error) {
      console.error('Error adding sound:', error);
      alert('Ошибка добавления звука');
    }
  };

  const deleteSound = async (soundName: string) => {
    if (!currentDeviceId) return;
    
    if (!window.confirm(`Удалить звук "${soundName}" из настроек уведомлений?`)) {
      return;
    }
    
    try {
      const sound = notificationSounds.find(s => s.name === soundName);
      if (!sound || sound.isCustom) return; // Нельзя удалять пользовательские звуки здесь
      
      // Удаляем из соответствующей таблицы используя ID
      if (sound.type === 'notification') {
        if (sound.id) {
          await apiClient.deleteNotificationSound(sound.id);
        }
      } else if (sound.type === 'excluded') {
        if (sound.id) {
          await apiClient.deleteExcludedSound(sound.id);
        }
      }
      
      // Обновляем локальное состояние
      setNotificationSounds(prev => prev.filter(s => s.name !== soundName));
    } catch (error) {
      console.error('Error deleting sound:', error);
      alert('Ошибка удаления звука');
    }
  };

  const filteredYamnetSounds = allSounds.filter(sound => 
    !notificationSounds.some(ns => ns.name.toLowerCase() === sound.toLowerCase()) &&
    sound.toLowerCase().includes(yamnetSearch.toLowerCase())
  );

  const getNotificationLabel = (type: string) => {
    switch (type) {
      case 'notification': return 'Уведомления';
      case 'excluded': return 'Исключены';
      default: return 'Без уведомлений';
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'notification': return 'bg-green-50 border-green-200';
      case 'excluded': return 'bg-red-50 border-red-200';
      default: return 'bg-gray-50 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка звуков...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex flex-col gap-4">
            {/* Заголовок */}
            <div className="flex items-center gap-3">
              <button
                onClick={onBack}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Настройки уведомлений</h1>
                <p className="text-sm text-gray-600">Управление звуками для уведомлений</p>
              </div>
            </div>
            
            {/* Кнопки действий */}
            <div className="flex flex-wrap gap-2 sm:gap-3">
              <button
                onClick={() => setShowYamnetModal(true)}
                className="flex-1 sm:flex-none px-4 py-2.5 h-10 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 flex items-center justify-center gap-2 text-sm font-medium transition-all duration-200 hover:scale-105 active:scale-95 shadow-lg hover:shadow-xl"
              >
                <Plus className="w-4 h-4" />
                <span className="hidden sm:inline">Добавить из YAMNet</span>
                <span className="sm:hidden">YAMNet</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Всего звуков</p>
              <p className="text-lg font-semibold text-blue-600">{allSounds.length}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Уведомления</p>
              <p className="text-lg font-semibold text-green-600">
                {notificationSounds.filter(s => s.type === 'notification').length}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Исключены</p>
              <p className="text-lg font-semibold text-red-600">
                {notificationSounds.filter(s => s.type === 'excluded').length}
              </p>
            </div>
          </div>
        </div>

        {/* Search and Filter */}
        <div className="bg-white rounded-xl p-4 sm:p-6 shadow-sm mt-4">
          <div className="flex flex-col gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Поиск звуков..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            {/* Filter buttons */}
            <div className="flex flex-wrap gap-2">
              <div className="flex gap-2 w-full sm:w-auto">
                <button
                  onClick={() => setFilter('all')}
                  className={`flex-1 sm:flex-none px-3 py-2 rounded-lg transition-colors text-sm font-medium ${
                    filter === 'all' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Все
                </button>
                <button
                  onClick={() => setFilter('notification')}
                  className={`flex-1 sm:flex-none px-3 py-2 rounded-lg transition-colors text-sm font-medium ${
                    filter === 'notification' 
                      ? 'bg-green-600 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Уведомления
                </button>
              </div>
              <div className="flex gap-2 w-full sm:w-auto">
                <button
                  onClick={() => setFilter('excluded')}
                  className={`flex-1 sm:flex-none px-3 py-2 rounded-lg transition-colors text-sm font-medium ${
                    filter === 'excluded' 
                      ? 'bg-red-600 text-white' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Исключены
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Sounds List */}
        <div className="bg-white rounded-xl shadow-sm mt-4 overflow-hidden">
          <div className="max-h-96 overflow-y-auto">
            {filteredSounds.length === 0 ? (
              <div className="text-center py-12">
                <Filter className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 text-lg">Звуки не найдены</p>
                <p className="text-gray-400 text-sm mt-2">Попробуйте изменить поиск или фильтр</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {filteredSounds.map((sound, index) => (
                  <div
                    key={`${sound.name}-${index}`}
                    className={`p-3 hover:bg-gray-50 transition-colors cursor-pointer ${getNotificationColor(sound.type)}`}
                    onClick={() => toggleNotificationType(sound.name)}
                  >
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 items-center">
                      
                      {/* Колонка 1: Название и состояние */}
                      <div className="flex items-center gap-2">
                        <span className="text-xl">{sound.icon}</span>
                        <div className="min-w-0 flex-1">
                          <h3 className="font-semibold text-gray-900 text-sm truncate">{sound.name}</h3>
                          <p className="text-xs text-gray-600 truncate">{getNotificationLabel(sound.type)}</p>
                        </div>
                      </div>
                      
                      {/* Колонка 2: Колокольчик (состояние) */}
                      <div className="flex justify-center">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                          sound.type === 'notification' ? 'bg-green-500' : 
                          sound.type === 'excluded' ? 'bg-red-500' : 'bg-gray-300'
                        }`}>
                          <Bell className="w-3 h-3 text-white" />
                        </div>
                      </div>
                      
                      {/* Колонка 3: Тип источника */}
                      <div className="text-center">
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          sound.isCustom 
                            ? 'bg-purple-100 text-purple-700' 
                            : 'bg-blue-100 text-blue-700'
                        }`}>
                          {sound.isCustom ? 'Польз.' : 'YamNET'}
                        </span>
                      </div>
                      
                      {/* Колонка 4: Мусорка (удаление) */}
                      <div className="flex justify-center">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteSound(sound.name);
                          }}
                          disabled={sound.isCustom}
                          className={`p-1.5 rounded-lg transition-colors ${
                            sound.isCustom 
                              ? 'bg-gray-100 cursor-not-allowed opacity-40' 
                              : 'hover:bg-red-50 group'
                          }`}
                          title={sound.isCustom ? 'Удалить из настроек' : 'Удалить звук'}
                        >
                          <Trash2 className={`w-4 h-4 ${
                            sound.isCustom 
                              ? 'text-gray-300 line-through' 
                              : 'text-gray-400 group-hover:text-red-600'
                          }`} />
                        </button>
                      </div>
                      
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Instructions */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 mt-4">
          <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Как это работает
          </h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• <strong>Уведомления:</strong> Вы будете получать уведомления на эти звуки</li>
            <li>• <strong>Исключены:</strong> Эти звуки не будут вызывать уведомления</li>
            <li>• <strong>Без уведомлений:</strong> Нейтральные звуки без уведомлений</li>
            <li>• Кликните на любой звук чтобы изменить его тип</li>
            <li>• Добавляйте пользовательские звуки для специфических нужд</li>
          </ul>
        </div>
      </div>

      {/* Add Custom Sound Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-2 sm:p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md animate-in fade-in zoom-in duration-300">
            <div className="p-4 sm:p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Добавить пользовательский звук</h3>
              <input
                type="text"
                placeholder="Название звука..."
                value={customSound}
                onChange={(e) => setCustomSound(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent mb-4"
                autoFocus
              />
              <div className="flex gap-2">
                <button
                  onClick={addCustomSound}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors active:scale-95"
                >
                  Добавить
                </button>
                <button
                  onClick={() => {
                    setShowAddModal(false);
                    setCustomSound('');
                  }}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors active:scale-95"
                >
                  Отмена
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* YAMNet Sounds Modal */}
      {showYamnetModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-2 sm:p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg sm:max-w-2xl max-h-[90vh] sm:max-h-[80vh] animate-in fade-in zoom-in duration-300 flex flex-col">
            <div className="p-4 sm:p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Выберите звук из YAMNet</h3>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Поиск звуков..."
                  value={yamnetSearch}
                  onChange={(e) => setYamnetSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  autoFocus
                />
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-3 sm:p-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 max-h-96">
                {filteredYamnetSounds.map((sound) => (
                  <button
                    key={sound}
                    onClick={() => addYamnetSound(sound)}
                    className="flex items-center gap-2 p-2 text-left hover:bg-gray-50 rounded-lg transition-colors border border-gray-200 active:scale-95"
                  >
                    <span className="text-lg sm:text-xl">{getSoundIcon(sound)}</span>
                    <span className="text-xs sm:text-sm font-medium text-gray-900 truncate">{sound}</span>
                  </button>
                ))}
              </div>
              {filteredYamnetSounds.length === 0 && (
                <div className="text-center py-8">
                  <p className="text-gray-500">Звуки не найдены</p>
                </div>
              )}
            </div>
            <div className="p-4 sm:p-6 border-t">
              <button
                onClick={() => {
                  setShowYamnetModal(false);
                  setYamnetSearch('');
                }}
                className="w-full px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors active:scale-95"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
