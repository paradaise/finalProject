import { X, Mic, Check, Loader, Radio, Wind, Clock, Volume2 } from 'lucide-react';
import { useState, useEffect } from 'react';

type Props = {
  title: string;
  description: string;
  onClose: () => void;
  onSave: (name: string, icon: string, duration: number) => void;
  color: 'purple' | 'red';
};

type RecordingState = 'idle' | 'recording' | 'analyzing' | 'complete';

export function RecordSoundModal({ title, description, onClose, onSave, color }: Props) {
  const [state, setState] = useState<RecordingState>('idle');
  const [recordingTime, setRecordingTime] = useState(0);
  const [soundName, setSoundName] = useState('');
  const [selectedIcon, setSelectedIcon] = useState('radio');

  const colorClasses = {
    purple: {
      bg: 'bg-purple-600',
      bgHover: 'bg-purple-700',
      bgLight: 'bg-purple-100',
      text: 'text-purple-600',
      border: 'border-purple-500',
    },
    red: {
      bg: 'bg-red-600',
      bgHover: 'bg-red-700',
      bgLight: 'bg-red-100',
      text: 'text-red-600',
      border: 'border-red-500',
    },
  };

  const colors = colorClasses[color];

  const availableIcons = [
    { id: 'radio', icon: Radio, label: 'Radio' },
    { id: 'wind', icon: Wind, label: 'Wind' },
    { id: 'clock', icon: Clock, label: 'Clock' },
    { id: 'volume', icon: Volume2, label: 'Volume' },
  ];

  useEffect(() => {
    let interval: number;
    if (state === 'recording') {
      interval = setInterval(() => {
        setRecordingTime(prev => {
          if (prev >= 10) {
            setState('analyzing');
            return prev;
          }
          return prev + 0.1;
        });
      }, 100);
    }
    return () => clearInterval(interval);
  }, [state]);

  useEffect(() => {
    if (state === 'analyzing') {
      const timeout = setTimeout(() => {
        setState('complete');
      }, 2000);
      return () => clearTimeout(timeout);
    }
  }, [state]);

  const handleStartRecording = () => {
    setState('recording');
    setRecordingTime(0);
  };

  const handleStopRecording = () => {
    setState('analyzing');
  };

  const handleSave = () => {
    if (soundName) {
      onSave(soundName, selectedIcon, recordingTime);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-50 animate-in fade-in">
      <div className="bg-white rounded-t-3xl w-full max-w-md animate-in slide-in-from-bottom duration-300 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 sticky top-0 bg-white">
          <div>
            <h2 className="text-gray-900 mb-1">{title}</h2>
            <p className="text-gray-600 text-sm">{description}</p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors flex-shrink-0"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        <div className="p-6">
          {/* Recording Interface */}
          {state === 'idle' && (
            <div className="text-center py-8">
              <div className={`w-24 h-24 ${colors.bgLight} rounded-full flex items-center justify-center mx-auto mb-6`}>
                <Mic className={`w-12 h-12 ${colors.text}`} />
              </div>
              <p className="text-gray-700 mb-6">
                Tap the button below to start recording
              </p>
              <button
                onClick={handleStartRecording}
                className={`w-full ${colors.bg} text-white py-4 rounded-xl active:${colors.bgHover} transition-colors`}
              >
                Start Recording
              </button>
            </div>
          )}

          {state === 'recording' && (
            <div className="text-center py-8">
              <div className={`w-24 h-24 ${colors.bgLight} rounded-full flex items-center justify-center mx-auto mb-6 animate-pulse`}>
                <Mic className={`w-12 h-12 ${colors.text}`} />
              </div>
              <div className={`text-4xl ${colors.text} mb-2`}>
                {recordingTime.toFixed(1)}s
              </div>
              <p className="text-gray-600 mb-6">
                Recording in progress...
              </p>
              <div className="w-full bg-gray-100 h-2 rounded-full mb-6">
                <div 
                  className={`h-full ${colors.bg} rounded-full transition-all`}
                  style={{ width: `${(recordingTime / 10) * 100}%` }}
                />
              </div>
              <button
                onClick={handleStopRecording}
                className="w-full bg-gray-700 text-white py-4 rounded-xl active:bg-gray-800 transition-colors"
              >
                Stop Recording
              </button>
            </div>
          )}

          {state === 'analyzing' && (
            <div className="text-center py-8">
              <div className={`w-24 h-24 ${colors.bgLight} rounded-full flex items-center justify-center mx-auto mb-6`}>
                <Loader className={`w-12 h-12 ${colors.text} animate-spin`} />
              </div>
              <p className="text-gray-900 mb-2">Analyzing sound...</p>
              <p className="text-gray-600">
                Processing your recording
              </p>
            </div>
          )}

          {state === 'complete' && (
            <div className="space-y-6">
              <div className="text-center py-4">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Check className="w-8 h-8 text-green-600" />
                </div>
                <p className="text-gray-900">Recording complete!</p>
                <p className="text-gray-600 text-sm">Duration: {recordingTime.toFixed(1)}s</p>
              </div>

              {/* Name Input */}
              <div>
                <label className="block text-gray-700 mb-2 text-sm">Sound Name</label>
                <input
                  type="text"
                  value={soundName}
                  onChange={(e) => setSoundName(e.target.value)}
                  placeholder="e.g., Refrigerator Hum"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  autoFocus
                />
              </div>

              {/* Icon Selection */}
              <div>
                <label className="block text-gray-700 mb-3 text-sm">Choose Icon</label>
                <div className="grid grid-cols-4 gap-3">
                  {availableIcons.map((item) => {
                    const IconComponent = item.icon;
                    return (
                      <button
                        key={item.id}
                        onClick={() => setSelectedIcon(item.id)}
                        className={`p-4 rounded-xl border-2 transition-all ${
                          selectedIcon === item.id
                            ? `${colors.border} ${colors.bgLight}`
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <IconComponent className={`w-6 h-6 mx-auto ${
                          selectedIcon === item.id ? colors.text : 'text-gray-600'
                        }`} />
                        <p className="text-xs text-gray-600 mt-2">{item.label}</p>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Save Button */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={onClose}
                  className="flex-1 py-3 border border-gray-300 rounded-xl text-gray-700 active:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={!soundName}
                  className={`flex-1 py-3 ${colors.bg} text-white rounded-xl active:${colors.bgHover} disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  Save Sound
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
