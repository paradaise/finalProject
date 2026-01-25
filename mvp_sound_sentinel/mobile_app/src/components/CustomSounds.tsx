import { useState } from 'react';
import { ArrowLeft, VolumeX, Zap, Plus, Trash2, X } from 'lucide-react';
import { AudioRecorder } from './AudioRecorder';
import { apiClient } from '../api/client';

interface Props {
  sounds: any[];
  onBack: () => void;
  onRefresh: () => void;
  selectedDeviceId?: string;
}

export function CustomSounds({ sounds, onBack, onRefresh, selectedDeviceId }: Props) {
  const excludedSounds = sounds.filter(s => s.sound_type === 'excluded');
  const specificSounds = sounds.filter(s => s.sound_type === 'specific');
  
  const [showAddModal, setShowAddModal] = useState(false);
  const [soundType, setSoundType] = useState<'excluded' | 'specific'>('excluded');
  const [soundName, setSoundName] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordings, setRecordings] = useState<Float32Array[]>([]);

  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleDateString('ru-RU');
    } catch {
      return timestamp;
    }
  };

  const handleDeleteSound = async (soundId: string) => {
    try {
      await apiClient.deleteCustomSound(soundId);
      onRefresh();
    } catch (error) {
      console.error('Error deleting sound:', error);
      alert('Ошибка удаления звука');
    }
  };

  const handleRecordComplete = (audioData: Float32Array) => {
    setRecordings(prev => [...prev, audioData]);
    
    // Если записали 3 раза, автоматически добавляем звук
    if (recordings.length >= 2) {
      handleAddSound();
    }
  };

  const handleAddSound = async () => {
    if (!soundName.trim() || recordings.length === 0 || !selectedDeviceId) {
      alert('Заполните название звука и запишите его хотя бы 1 раз');
      return;
    }

    try {
      // Усредняем MFCC признаки из всех записей
      const mfccFeatures = await extractAverageMFCC(recordings);
      
      await apiClient.addCustomSound(soundName, soundType, mfccFeatures, selectedDeviceId);
      
      // Сброс формы
      setSoundName('');
      setRecordings([]);
      setShowAddModal(false);
      onRefresh();
      
      alert(`Звук "${soundName}" успешно добавлен!`);
    } catch (error) {
      console.error('Error adding sound:', error);
      alert('Ошибка добавления звука');
    }
  };

  const extractAverageMFCC = async (audioBuffers: Float32Array[]): Promise<number[]> => {
    // Простая реализация - усредняем значения аудио
    // В реальном приложении здесь должна быть полноценная MFCC экстракция
    const allFeatures: number[] = [];
    
    for (const audioBuffer of audioBuffers) {
      // Усредняем значения аудио как простые признаки
      const mean = audioBuffer.reduce((sum, val) => sum + val, 0) / audioBuffer.length;
      const std = Math.sqrt(audioBuffer.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / audioBuffer.length);
      
      allFeatures.push(mean, std);
    }
    
    // Возвращаем усредненные признаки
    const featureSize = 2; // mean и std
    const averagedFeatures: number[] = [];
    
    for (let i = 0; i < featureSize; i++) {
      let sum = 0;
      for (let j = 0; j < allFeatures.length; j += featureSize) {
        sum += allFeatures[j + i] || 0;
      }
      averagedFeatures.push(sum / audioBuffers.length);
    }
    
    return averagedFeatures;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h1 className="text-xl font-semibold">Пользовательские звуки</h1>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6 space-y-8">
        {/* Excluded Sounds */}
        <div>
          <div className="flex items-center gap-3 mb-4">
            <VolumeX className="w-6 h-6 text-purple-600" />
            <h2 className="text-lg font-semibold text-gray-900">Исключенные звуки</h2>
            <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">
              {excludedSounds.length}
            </span>
          </div>

          {excludedSounds.length === 0 ? (
            <div className="bg-white rounded-xl p-8 text-center shadow-sm border-2 border-dashed border-gray-200">
              <VolumeX className="w-12 h-12 mx-auto text-gray-300 mb-3" />
              <h3 className="text-md font-medium text-gray-600 mb-2">Нет исключенных звуков</h3>
              <p className="text-sm text-gray-500">Добавьте звуки, которые нужно игнорировать</p>
            </div>
          ) : (
            <div className="space-y-3">
              {excludedSounds.map((sound) => (
                <div
                  key={sound.id}
                  className="bg-white rounded-xl p-4 shadow-sm border-l-4 border-purple-500"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-gray-900">{sound.name}</h3>
                      <p className="text-sm text-gray-600">Добавлен: {formatTime(sound.created_at)}</p>
                    </div>
                    <button
                      onClick={() => handleDeleteSound(sound.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Specific Sounds */}
        <div>
          <div className="flex items-center gap-3 mb-4">
            <Zap className="w-6 h-6 text-green-600" />
            <h2 className="text-lg font-semibold text-gray-900">Важные звуки</h2>
            <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-sm">
              {specificSounds.length}
            </span>
          </div>

          {specificSounds.length === 0 ? (
            <div className="bg-white rounded-xl p-8 text-center shadow-sm border-2 border-dashed border-gray-200">
              <Zap className="w-12 h-12 mx-auto text-gray-300 mb-3" />
              <h3 className="text-md font-medium text-gray-600 mb-2">Нет важных звуков</h3>
              <p className="text-sm text-gray-500">Добавьте звуки для немедленных уведомлений</p>
            </div>
          ) : (
            <div className="space-y-3">
              {specificSounds.map((sound) => (
                <div
                  key={sound.id}
                  className="bg-white rounded-xl p-4 shadow-sm border-l-4 border-green-500"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-gray-900">{sound.name}</h3>
                      <p className="text-sm text-gray-600">Добавлен: {formatTime(sound.created_at)}</p>
                    </div>
                    <button
                      onClick={() => handleDeleteSound(sound.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Add Buttons */}
        <div className="grid grid-cols-2 gap-4">
          <button 
            onClick={() => {
              setSoundType('excluded');
              setShowAddModal(true);
            }}
            className="bg-purple-600 text-white py-3 px-4 rounded-xl flex items-center justify-center gap-2 hover:bg-purple-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            Добавить исключенный
          </button>
          <button 
            onClick={() => {
              setSoundType('specific');
              setShowAddModal(true);
            }}
            className="bg-green-600 text-white py-3 px-4 rounded-xl flex items-center justify-center gap-2 hover:bg-green-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            Добавить важный
          </button>
        </div>
      </div>

      {/* Add Sound Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">
                Добавить {soundType === 'excluded' ? 'исключенный' : 'важный'} звук
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-1 hover:bg-gray-100 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Название звука
                </label>
                <input
                  type="text"
                  value={soundName}
                  onChange={(e) => setSoundName(e.target.value)}
                  placeholder="Например: дверной звонок"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Запись звука ({recordings.length + 1}/3)
                </label>
                <AudioRecorder
                  onRecordComplete={handleRecordComplete}
                  isRecording={isRecording}
                  setIsRecording={setIsRecording}
                />
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Отмена
                </button>
                <button
                  onClick={handleAddSound}
                  disabled={!soundName.trim() || recordings.length === 0}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Добавить звук
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
