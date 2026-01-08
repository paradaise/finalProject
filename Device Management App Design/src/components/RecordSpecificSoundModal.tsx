import { X, Mic, Check, Loader, Baby, Bell, AlertTriangle, Dog, Volume2, Flame } from 'lucide-react';
import { useState, useEffect } from 'react';

type Props = {
  onClose: () => void;
  onSave: (name: string, icon: string, priority: 'low' | 'medium' | 'high', duration: number) => void;
};

type RecordingState = 'idle' | 'recording' | 'analyzing' | 'segmenting' | 'complete';

export function RecordSpecificSoundModal({ onClose, onSave }: Props) {
  const [state, setState] = useState<RecordingState>('idle');
  const [recordingTime, setRecordingTime] = useState(0);
  const [soundName, setSoundName] = useState('');
  const [selectedIcon, setSelectedIcon] = useState('bell');
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('high');
  const [selectedSegment, setSelectedSegment] = useState(0);

  const availableIcons = [
    { id: 'baby', icon: Baby, label: 'Baby' },
    { id: 'bell', icon: Bell, label: 'Bell' },
    { id: 'alert-triangle', icon: AlertTriangle, label: 'Alert' },
    { id: 'dog', icon: Dog, label: 'Dog' },
    { id: 'volume', icon: Volume2, label: 'Volume' },
    { id: 'flame', icon: Flame, label: 'Alarm' },
  ];

  const segments = [
    { id: 0, start: 0, duration: 2.1, quality: 95 },
    { id: 1, start: 2.5, duration: 1.8, quality: 88 },
    { id: 2, start: 5.2, duration: 2.3, quality: 92 },
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
        setState('segmenting');
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

  const handleSelectSegment = (segmentId: number) => {
    setSelectedSegment(segmentId);
    setState('complete');
  };

  const handleSave = () => {
    if (soundName) {
      const segment = segments[selectedSegment];
      onSave(soundName, selectedIcon, priority, segment.duration);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-50 animate-in fade-in">
      <div className="bg-white rounded-t-3xl w-full max-w-md animate-in slide-in-from-bottom duration-300 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 sticky top-0 bg-white">
          <div>
            <h2 className="text-gray-900 mb-1">Record Specific Sound</h2>
            <p className="text-gray-600 text-sm">Record a sound you want to track</p>
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
              <div className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <Mic className="w-12 h-12 text-red-600" />
              </div>
              <p className="text-gray-700 mb-6">
                Position the device near the sound source and start recording
              </p>
              <button
                onClick={handleStartRecording}
                className="w-full bg-red-600 text-white py-4 rounded-xl active:bg-red-700 transition-colors"
              >
                Start Recording
              </button>
            </div>
          )}

          {state === 'recording' && (
            <div className="text-center py-8">
              <div className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6 animate-pulse">
                <Mic className="w-12 h-12 text-red-600" />
              </div>
              <div className="text-4xl text-red-600 mb-2">
                {recordingTime.toFixed(1)}s
              </div>
              <p className="text-gray-600 mb-6">
                Recording... Trigger the sound now
              </p>
              <div className="w-full bg-gray-100 h-2 rounded-full mb-6">
                <div 
                  className="h-full bg-red-600 rounded-full transition-all"
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
              <div className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <Loader className="w-12 h-12 text-red-600 animate-spin" />
              </div>
              <p className="text-gray-900 mb-2">Analyzing recording...</p>
              <p className="text-gray-600">
                Detecting sound patterns
              </p>
            </div>
          )}

          {state === 'segmenting' && (
            <div className="space-y-6">
              <div className="text-center">
                <p className="text-gray-900 mb-2">Select Best Segment</p>
                <p className="text-gray-600 text-sm">
                  We found {segments.length} potential sound segments
                </p>
              </div>

              <div className="space-y-3">
                {segments.map((segment) => (
                  <button
                    key={segment.id}
                    onClick={() => handleSelectSegment(segment.id)}
                    className="w-full p-4 border-2 border-gray-200 rounded-xl hover:border-red-500 transition-all text-left"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-900">Segment {segment.id + 1}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-green-500" />
                        <span className="text-green-700 text-sm">{segment.quality}% match</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 text-gray-600 text-sm">
                      <span>Start: {segment.start.toFixed(1)}s</span>
                      <span>·</span>
                      <span>Duration: {segment.duration.toFixed(1)}s</span>
                    </div>
                    <div className="mt-3 h-12 bg-gray-100 rounded-lg relative overflow-hidden">
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="w-full h-full flex items-end justify-around gap-0.5 px-2">
                          {Array.from({ length: 30 }).map((_, i) => (
                            <div
                              key={i}
                              className="flex-1 bg-red-400 rounded-t"
                              style={{ height: `${Math.random() * 100}%` }}
                            />
                          ))}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {state === 'complete' && (
            <div className="space-y-6">
              <div className="text-center py-4">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Check className="w-8 h-8 text-green-600" />
                </div>
                <p className="text-gray-900">Segment selected!</p>
                <p className="text-gray-600 text-sm">
                  Duration: {segments[selectedSegment].duration.toFixed(1)}s
                </p>
              </div>

              {/* Name Input */}
              <div>
                <label className="block text-gray-700 mb-2 text-sm">Sound Name</label>
                <input
                  type="text"
                  value={soundName}
                  onChange={(e) => setSoundName(e.target.value)}
                  placeholder="e.g., Baby Crying"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  autoFocus
                />
              </div>

              {/* Priority Selection */}
              <div>
                <label className="block text-gray-700 mb-3 text-sm">Priority Level</label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { value: 'low' as const, label: 'Low', color: 'blue' },
                    { value: 'medium' as const, label: 'Medium', color: 'yellow' },
                    { value: 'high' as const, label: 'High', color: 'red' },
                  ].map((item) => (
                    <button
                      key={item.value}
                      onClick={() => setPriority(item.value)}
                      className={`py-3 rounded-xl border-2 transition-all ${
                        priority === item.value
                          ? `border-${item.color}-500 bg-${item.color}-50 text-${item.color}-700`
                          : 'border-gray-200 text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Icon Selection */}
              <div>
                <label className="block text-gray-700 mb-3 text-sm">Choose Icon</label>
                <div className="grid grid-cols-3 gap-3">
                  {availableIcons.map((item) => {
                    const IconComponent = item.icon;
                    return (
                      <button
                        key={item.id}
                        onClick={() => setSelectedIcon(item.id)}
                        className={`p-4 rounded-xl border-2 transition-all ${
                          selectedIcon === item.id
                            ? 'border-red-500 bg-red-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <IconComponent className={`w-6 h-6 mx-auto ${
                          selectedIcon === item.id ? 'text-red-600' : 'text-gray-600'
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
                  className="flex-1 py-3 bg-red-600 text-white rounded-xl active:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
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
