import { ArrowLeft, Plus, VolumeX } from 'lucide-react';
import { useState } from 'react';
import { ExcludedSound } from '../App';
import { SoundItem } from './SoundItem';
import { RecordSoundModal } from './RecordSoundModal';

type Props = {
  excludedSounds: ExcludedSound[];
  onBack: () => void;
  onAddSound: (sound: Omit<ExcludedSound, 'id'>) => void;
  onDeleteSound: (soundId: string) => void;
};

export function ExcludingSoundsScreen({ 
  excludedSounds, 
  onBack, 
  onAddSound,
  onDeleteSound 
}: Props) {
  const [showRecordModal, setShowRecordModal] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-50 to-gray-50">
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
              <h1 className="text-gray-900">Excluding Sounds</h1>
            </div>
          </div>
          <p className="text-gray-600 ml-13">
            Sounds that will be ignored during monitoring
          </p>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 py-6">
        {/* Info Card */}
        <div className="bg-purple-50 border border-purple-200 rounded-2xl p-4 mb-6">
          <div className="flex gap-3">
            <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center flex-shrink-0">
              <VolumeX className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-purple-900 mb-1">How It Works</p>
              <p className="text-purple-700 text-sm">
                Place your device near the sound source and record it. The system will learn to ignore this sound during monitoring.
              </p>
            </div>
          </div>
        </div>

        {/* Excluded Sounds List */}
        {excludedSounds.length > 0 ? (
          <div className="space-y-3 mb-6">
            {excludedSounds.map((sound) => (
              <SoundItem
                key={sound.id}
                sound={sound}
                onDelete={() => onDeleteSound(sound.id)}
                color="purple"
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-16 mb-6">
            <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <VolumeX className="w-10 h-10 text-purple-400" />
            </div>
            <p className="text-gray-900 mb-2">No excluded sounds yet</p>
            <p className="text-gray-600 text-sm px-8">
              Add sounds that you want the system to ignore, like appliances or background noise
            </p>
          </div>
        )}

        {/* Add Sound Button */}
        <button
          onClick={() => setShowRecordModal(true)}
          className="w-full bg-purple-600 text-white py-4 rounded-xl flex items-center justify-center gap-2 active:bg-purple-700 transition-colors shadow-sm"
        >
          <Plus className="w-5 h-5" />
          Add Excluded Sound
        </button>
      </div>

      {/* Record Sound Modal */}
      {showRecordModal && (
        <RecordSoundModal
          title="Record Excluded Sound"
          description="Place the device near the sound source you want to exclude"
          onClose={() => setShowRecordModal(false)}
          onSave={(name, icon, duration) => {
            onAddSound({
              name,
              icon,
              recordedAt: new Date(),
              duration,
            });
            setShowRecordModal(false);
          }}
          color="purple"
        />
      )}
    </div>
  );
}
