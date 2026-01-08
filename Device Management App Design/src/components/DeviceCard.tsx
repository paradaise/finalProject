import { Cpu, Thermometer, Wifi, WifiOff, AlertTriangle, Trash2 } from 'lucide-react';
import { Device } from '../App';
import { useState } from 'react';

type Props = {
  device: Device;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: () => void;
};

export function DeviceCard({ device, isSelected, onSelect, onDelete }: Props) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const statusConfig = {
    online: {
      color: 'bg-green-500',
      icon: Wifi,
      text: 'Online',
      textColor: 'text-green-700',
      bgColor: 'bg-green-50',
    },
    offline: {
      color: 'bg-gray-400',
      icon: WifiOff,
      text: 'Offline',
      textColor: 'text-gray-600',
      bgColor: 'bg-gray-50',
    },
    error: {
      color: 'bg-red-500',
      icon: AlertTriangle,
      text: 'Error',
      textColor: 'text-red-700',
      bgColor: 'bg-red-50',
    },
  };

  const config = statusConfig[device.status];
  const StatusIcon = config.icon;

  const formatLastSeen = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  return (
    <div
      onClick={onSelect}
      className={`bg-white rounded-2xl p-4 shadow-sm border-2 transition-all ${
        isSelected ? 'border-blue-500 shadow-md' : 'border-transparent'
      } active:scale-98`}
    >
      <div className="flex items-start gap-4">
        {/* Device Icon */}
        <div className={`w-14 h-14 ${config.bgColor} rounded-xl flex items-center justify-center flex-shrink-0`}>
          <Cpu className={`w-7 h-7 ${config.textColor}`} />
        </div>

        {/* Device Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-2">
            <h3 className="text-gray-900 truncate">{device.name}</h3>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowDeleteConfirm(true);
              }}
              className="text-gray-400 hover:text-red-600 transition-colors p-1"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>

          {/* Status Badge */}
          <div className="flex items-center gap-2 mb-3">
            <div className={`w-2 h-2 rounded-full ${config.color}`} />
            <span className={`text-sm ${config.textColor}`}>{config.text}</span>
            {device.status !== 'offline' && (
              <span className="text-gray-500 text-sm">· {formatLastSeen(device.lastSeen)}</span>
            )}
          </div>

          {/* Technical Details */}
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <StatusIcon className="w-3.5 h-3.5 text-gray-400" />
              <span className="text-gray-600 text-sm">{device.ipAddress}</span>
            </div>
            <div className="text-gray-500 text-sm font-mono">
              {device.macAddress}
            </div>
          </div>

          {/* Health Indicators */}
          {device.status === 'online' && device.temperature && device.cpuLoad && (
            <div className="flex items-center gap-4 mt-3 pt-3 border-t border-gray-100">
              <div className="flex items-center gap-1.5">
                <Thermometer className="w-4 h-4 text-orange-500" />
                <span className="text-sm text-gray-700">{device.temperature}°C</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Cpu className="w-4 h-4 text-blue-500" />
                <span className="text-sm text-gray-700">{device.cpuLoad}%</span>
              </div>
            </div>
          )}

          {/* Error State */}
          {device.status === 'error' && (
            <div className="mt-3 pt-3 border-t border-red-100">
              <p className="text-red-600 text-sm">Device not sending data. Check connection.</p>
            </div>
          )}
        </div>
      </div>

      {/* Delete Confirmation */}
      {showDeleteConfirm && (
        <div 
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={(e) => {
            e.stopPropagation();
            setShowDeleteConfirm(false);
          }}
        >
          <div 
            className="bg-white rounded-2xl p-6 max-w-sm w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-gray-900 mb-2">Delete Device?</h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to remove "{device.name}"? This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowDeleteConfirm(false);
                }}
                className="flex-1 py-3 border border-gray-300 rounded-xl text-gray-700 active:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete();
                }}
                className="flex-1 py-3 bg-red-600 text-white rounded-xl active:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
