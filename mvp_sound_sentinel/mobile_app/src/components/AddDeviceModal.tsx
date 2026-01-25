import React, { useState } from 'react';
import { X, Monitor, Smartphone } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onAddDevice: (device: any) => void;
}

export function AddDeviceModal({ isOpen, onClose, onAddDevice }: Props) {
  const [formData, setFormData] = useState({
    name: '',
    ip_address: '',
    mac_address: '',
    model: 'Raspberry Pi',
    microphone_info: 'Default Microphone',
    wifi_signal: 50
  });

  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await fetch('http://192.168.0.61:8000/register_device', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        const result = await response.json();
        onAddDevice({ ...formData, id: result.device_id, status: 'online' });
        onClose();
        setFormData({
          name: '',
          ip_address: '',
          mac_address: '',
          model: 'Raspberry Pi',
          microphone_info: 'Default Microphone',
          wifi_signal: 50
        });
      } else {
        alert('Ошибка добавления устройства');
      }
    } catch (error) {
      alert('Ошибка подключения к серверу');
    } finally {
      setIsLoading(false);
    }
  };

  const deviceTypes = [
    { value: 'Raspberry Pi', label: 'Raspberry Pi', icon: Monitor },
    { value: 'Smartphone', label: 'Смартфон', icon: Smartphone },
    { value: 'Custom', label: 'Другое', icon: Monitor },
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">Добавить устройство</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Название устройства */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Название устройства
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Например: Raspberry Pi Monitor"
            />
          </div>

          {/* IP адрес */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              IP адрес
            </label>
            <input
              type="text"
              required
              pattern="^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
              value={formData.ip_address}
              onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="192.168.0.100"
            />
          </div>

          {/* MAC адрес */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              MAC адрес
            </label>
            <input
              type="text"
              required
              pattern="^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
              value={formData.mac_address}
              onChange={(e) => setFormData({ ...formData, mac_address: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
              placeholder="68:A2:8B:2C:B1:C6"
            />
          </div>

          {/* Тип устройства */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Тип устройства
            </label>
            <select
              value={formData.model}
              onChange={(e) => setFormData({ ...formData, model: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {deviceTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* Микрофон */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Микрофон
            </label>
            <input
              type="text"
              value={formData.microphone_info}
              onChange={(e) => setFormData({ ...formData, microphone_info: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Default Microphone"
            />
          </div>

          {/* WiFi сигнал */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              WiFi сигнал: {formData.wifi_signal}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={formData.wifi_signal}
              onChange={(e) => setFormData({ ...formData, wifi_signal: parseInt(e.target.value) })}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>

          {/* Кнопки */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Отмена
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Добавление...' : 'Добавить'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
