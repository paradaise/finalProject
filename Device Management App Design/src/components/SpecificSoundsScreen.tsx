import { ArrowLeft, Plus, Zap } from 'lucide-react';
import { useState } from 'react';
import { SpecificSound } from '../App';
import { SoundItem } from './SoundItem';
import { RecordSpecificSoundModal } from './RecordSpecificSoundModal';

type Props = {
  specificSounds: SpecificSound[];
  onBack: () => void;
  onAddSound: (sound: Omit<SpecificSound, 'id'>) => void;
  onDeleteSound: (soundId: string) => void;
};

export function SpecificSoundsScreen({ 
  specificSounds, 
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
    <div className="min-h-screen bg-gradient-to-b from-red-50 to-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 py-4">
          <div className="flex items-center gap-3 mb-2">
            <button
              onClick={onBack}
              className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-gray-700" />
            </button>
            <div className="flex-1">
              <h1 className="text-gray-900">Specific Sounds</h1>
            </div>
          </div>
          <p className="text-gray-600 ml-13">
            Important sounds the system should track
          </p>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 py-6">
        {/* Info Card */}
        <div className="bg-red-50 border border-red-200 rounded-2xl p-4 mb-6">
          <div className="flex gap-3">
            <div className="w-10 h-10 bg-red-100 rounded-xl flex items-center justify-center flex-shrink-0">
              <Zap className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-red-900 mb-1">Priority Tracking</p>
              <p className="text-red-700 text-sm">
                Record specific sounds you want to be notified about, like alarms, baby cries, or doorbells.
              </p>
            </div>
          </div>
        </div>

        {/* Priority Filter */}
        {specificSounds.length > 0 && (
          <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
            <button className="px-4 py-2 bg-white border-2 border-blue-500 text-blue-700 rounded-xl text-sm whitespace-nowrap">
              All ({specificSounds.length})
            </button>
            <button className="px-4 py-2 bg-white border border-gray-200 text-gray-700 rounded-xl text-sm whitespace-nowrap hover:border-gray-300">
              High Priority ({specificSounds.filter(s => s.priority === 'high').length})
            </button>
            <button className="px-4 py-2 bg-white border border-gray-200 text-gray-700 rounded-xl text-sm whitespace-nowrap hover:border-gray-300">
              Medium ({specificSounds.filter(s => s.priority === 'medium').length})
            </button>
          </div>
        )}

        {/* Specific Sounds List */}
        {specificSounds.length > 0 ? (
          <div className="space-y-3 mb-6">
            {specificSounds.map((sound) => (
              <div key={sound.id} className="relative">
                <SoundItem
                  sound={sound}
                  onDelete={() => onDeleteSound(sound.id)}
                  color="red"
                />
                <div className={`absolute top-4 right-4 px-3 py-1 rounded-full text-xs ${priorityBadges[sound.priority]}`}>
                  {sound.priority}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16 mb-6">
            <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Zap className="w-10 h-10 text-red-400" />
            </div>
            <p className="text-gray-900 mb-2">No specific sounds yet</p>
            <p className="text-gray-600 text-sm px-8">
              Add sounds that you want to track and be notified about
            </p>
          </div>
        )}

        {/* Add Sound Button */}
        <button
          onClick={() => setShowRecordModal(true)}
          className="w-full bg-red-600 text-white py-4 rounded-xl flex items-center justify-center gap-2 active:bg-red-700 transition-colors shadow-sm"
        >
          <Plus className="w-5 h-5" />
          Add Specific Sound
        </button>
      </div>

      {/* Record Sound Modal */}
      {showRecordModal && (
        <RecordSpecificSoundModal
          onClose={() => setShowRecordModal(false)}
          onSave={(name, icon, priority, duration) => {
            onAddSound({
              name,
              icon,
              priority,
              recordedAt: new Date(),
              duration,
            });
            setShowRecordModal(false);
          }}
        />
      )}
    </div>
  );
}
