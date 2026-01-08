import { X } from 'lucide-react';
import { useState } from 'react';
import { Device } from '../App';

type Props = {
  onClose: () => void;
  onAdd: (device: Omit<Device, 'id'>) => void;
};

export function AddDeviceModal({ onClose, onAdd }: Props) {
  const [name, setName] = useState('');
  const [ipAddress, setIpAddress] = useState('');
  const [macAddress, setMacAddress] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name || !ipAddress || !macAddress) return;

    onAdd({
      name,
      ipAddress,
      macAddress,
      status: 'offline',
      lastSeen: new Date(),
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-50 animate-in fade-in">
      <div className="bg-white rounded-t-3xl w-full max-w-md animate-in slide-in-from-bottom duration-300">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-gray-900">Add New Device</h2>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-4 mb-6">
            <div>
              <label className="block text-gray-700 mb-2 text-sm">Device Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Living Room Monitor"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 mb-2 text-sm">IP Address</label>
              <input
                type="text"
                value={ipAddress}
                onChange={(e) => setIpAddress(e.target.value)}
                placeholder="e.g., 192.168.1.105"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 mb-2 text-sm">MAC Address</label>
              <input
                type="text"
                value={macAddress}
                onChange={(e) => setMacAddress(e.target.value)}
                placeholder="e.g., B8:27:EB:XX:XX:XX"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                required
              />
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
            <p className="text-blue-900 text-sm mb-1">📡 Device Setup</p>
            <p className="text-blue-700 text-sm">
              Make sure your Raspberry Pi is connected to the network and running the audio monitoring software.
            </p>
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-3 border border-gray-300 rounded-xl text-gray-700 active:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 py-3 bg-blue-600 text-white rounded-xl active:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!name || !ipAddress || !macAddress}
            >
              Add Device
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
