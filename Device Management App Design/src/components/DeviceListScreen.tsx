import { Plus } from 'lucide-react';
import { useState } from 'react';
import { Device } from '../App';
import { DeviceCard } from './DeviceCard';
import { AddDeviceModal } from './AddDeviceModal';

type Props = {
  devices: Device[];
  selectedDeviceId: string | null;
  onSelectDevice: (deviceId: string) => void;
  onAddDevice: (device: Omit<Device, 'id'>) => void;
  onDeleteDevice: (deviceId: string) => void;
};

export function DeviceListScreen({ 
  devices, 
  selectedDeviceId, 
  onSelectDevice, 
  onAddDevice,
  onDeleteDevice 
}: Props) {
  const [showAddModal, setShowAddModal] = useState(false);

  const onlineCount = devices.filter(d => d.status === 'online').length;
  const errorCount = devices.filter(d => d.status === 'error').length;

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-gray-50 pb-20">
      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 py-6">
          <h1 className="text-gray-900 mb-1">Audio Monitors</h1>
          <p className="text-gray-600">
            {onlineCount} online · {devices.length} total
            {errorCount > 0 && <span className="text-red-600"> · {errorCount} error</span>}
          </p>
        </div>
      </div>

      {/* Device List */}
      <div className="max-w-md mx-auto px-4 pt-6">
        <div className="space-y-3">
          {devices.map((device) => (
            <DeviceCard
              key={device.id}
              device={device}
              isSelected={device.id === selectedDeviceId}
              onSelect={() => onSelectDevice(device.id)}
              onDelete={() => onDeleteDevice(device.id)}
            />
          ))}
        </div>

        {devices.length === 0 && (
          <div className="text-center py-16">
            <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Plus className="w-10 h-10 text-gray-400" />
            </div>
            <p className="text-gray-900 mb-2">No devices yet</p>
            <p className="text-gray-600 text-sm">Add your first audio monitor to get started</p>
          </div>
        )}
      </div>

      {/* Add Device Button */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4">
        <div className="max-w-md mx-auto">
          <button
            onClick={() => setShowAddModal(true)}
            className="w-full bg-blue-600 text-white py-4 rounded-xl flex items-center justify-center gap-2 active:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            Add New Device
          </button>
        </div>
      </div>

      {/* Add Device Modal */}
      {showAddModal && (
        <AddDeviceModal
          onClose={() => setShowAddModal(false)}
          onAdd={(device) => {
            onAddDevice(device);
            setShowAddModal(false);
          }}
        />
      )}
    </div>
  );
}
