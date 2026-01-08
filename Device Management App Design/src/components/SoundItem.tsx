import { Trash2, Radio, Wind, Clock, Baby, Bell, AlertTriangle, Dog, Volume2 } from 'lucide-react';
import { useState } from 'react';

type Sound = {
  id: string;
  name: string;
  icon: string;
  recordedAt: Date;
  duration: number;
};

type Props = {
  sound: Sound;
  onDelete: () => void;
  color: 'purple' | 'red';
};

export function SoundItem({ sound, onDelete, color }: Props) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const icons = {
    radio: Radio,
    wind: Wind,
    clock: Clock,
    baby: Baby,
    bell: Bell,
    'alert-triangle': AlertTriangle,
    dog: Dog,
    volume: Volume2,
  };

  const Icon = icons[sound.icon as keyof typeof icons] || Volume2;

  const colorClasses = {
    purple: 'bg-purple-100 text-purple-600',
    red: 'bg-red-100 text-red-600',
  };

  const formatDate = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <>
      <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
        <div className="flex items-start gap-4">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${colorClasses[color]}`}>
            <Icon className="w-6 h-6" />
          </div>
          
          <div className="flex-1 min-w-0">
            <h3 className="text-gray-900 mb-1">{sound.name}</h3>
            <div className="flex items-center gap-3 text-gray-600 text-sm">
              <span>{formatDate(sound.recordedAt)}</span>
              <span>·</span>
              <span>{sound.duration.toFixed(1)}s</span>
            </div>
          </div>

          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="text-gray-400 hover:text-red-600 transition-colors p-2"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Delete Confirmation */}
      {showDeleteConfirm && (
        <div 
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={() => setShowDeleteConfirm(false)}
        >
          <div 
            className="bg-white rounded-2xl p-6 max-w-sm w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-gray-900 mb-2">Delete Sound?</h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to remove "{sound.name}"? This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="flex-1 py-3 border border-gray-300 rounded-xl text-gray-700 active:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={onDelete}
                className="flex-1 py-3 bg-red-600 text-white rounded-xl active:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
