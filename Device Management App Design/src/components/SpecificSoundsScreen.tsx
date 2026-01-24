import { ArrowLeft, Plus, Zap } from 'lucide-react';
import { useState } from 'react';
import { SpecificSound } from '../api/client';
import { SoundItem } from './SoundItem';
import { RecordSpecificSoundModal } from './RecordSpecificSoundModal';

type Props = {
  sounds: SpecificSound[];
  onBack: () => void;
  onAddSound: (sound: Omit<SpecificSound, 'id'>) => void;
  onDeleteSound: (soundId: string) => void;
};

export function SpecificSoundsScreen({ 
  sounds, 
  onBack, 
  onAddSound,
  onDeleteSound 
}: Props) {
  const [showRecordModal, setShowRecordModal] = useState(false);

  const priorityBadges = {
    high: 'bg-red-100 text-red-700',
    medium: 'bg-yellow-100 text-yellow-700',
    low: 'bg-blue-100 text-blue-700',
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-green-50 to-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h1 className="text-xl font-semibold">Specific Sounds</h1>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Info Card */}
        <div className="bg-green-50 border border-green-200 rounded-xl p-6 mb-6">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-green-100 rounded-lg">
              <Zap className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-green-900 mb-1">How It Works</p>
              <p className="text-green-700 text-sm">
                Record important sounds you want to be notified about immediately. These sounds will trigger instant alerts.
              </p>
            </div>
          </div>
        </div>

        {/* Priority Stats */}
        {sounds.length > 0 && (
          <div className="grid grid-cols-3 gap-4 mb-6">
            {(['high', 'medium', 'low'] as const).map((priority) => (
              <div key={priority} className="bg-white rounded-lg p-4 text-center">
                <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${priorityBadges[priority]}`}>
                  {priority.charAt(0).toUpperCase() + priority.slice(1)}
                </div>
                <p className="text-2xl font-bold mt-2">
                  {sounds.filter((s) => s.priority === priority).length}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Specific Sounds List */}
        {sounds.length === 0 ? (
          <div className="text-center py-12">
            <Zap className="w-16 h-16 mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-medium text-gray-600 mb-2">No specific sounds</h3>
            <p className="text-gray-500 mb-6">Important sounds you want to track will appear here</p>
            <button
              onClick={() => setShowRecordModal(true)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              Add First Sound
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {sounds.map((sound) => (
              <SoundItem
                key={sound.id}
                sound={sound}
                onDelete={() => onDeleteSound(sound.id)}
                color="green"
                badge={priorityBadges[sound.priority]}
              />
            ))}
          </div>
        )}

        {/* Add Sound Button */}
        <button
          onClick={() => setShowRecordModal(true)}
          className="w-full bg-green-600 text-white py-4 rounded-xl flex items-center justify-center gap-2 active:bg-green-700 transition-colors shadow-sm"
        >
          <Plus className="w-5 h-5" />
          Add Specific Sound
        </button>
      </div>

      {/* Record Modal */}
      {showRecordModal && (
        <RecordSpecificSoundModal
          onClose={() => setShowRecordModal(false)}
          onAddSound={onAddSound}
        />
      )}
    </div>
  );
}
