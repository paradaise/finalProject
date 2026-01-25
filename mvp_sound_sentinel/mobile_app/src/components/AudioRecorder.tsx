import React, { useState, useRef } from 'react';
import { Mic, MicOff, Loader2 } from 'lucide-react';

interface Props {
  onRecordComplete: (audioData: Float32Array) => void;
  isRecording: boolean;
  setIsRecording: (recording: boolean) => void;
}

export function AudioRecorder({ onRecordComplete, isRecording, setIsRecording }: Props) {
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        setIsProcessing(true);
        
        try {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          const audioBuffer = await audioBlob.arrayBuffer();
          const audioContext = new AudioContext();
          const decodedAudio = await audioContext.decodeAudioData(audioBuffer);
          
          // Конвертируем в Float32Array (16kHz mono)
          const targetSampleRate = 16000;
          const resampledAudio = resampleAudio(decodedAudio, targetSampleRate);
          
          onRecordComplete(resampledAudio);
        } catch (error) {
          console.error('Error processing audio:', error);
        } finally {
          setIsProcessing(false);
        }
        
        // Останавливаем все треки
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Не удалось получить доступ к микрофону');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const resampleAudio = (audioBuffer: AudioBuffer, targetSampleRate: number): Float32Array => {
    const sourceSampleRate = audioBuffer.sampleRate;
    const sourceLength = audioBuffer.length;
    const targetLength = Math.floor(sourceLength * targetSampleRate / sourceSampleRate);
    
    const resampled = new Float32Array(targetLength);
    const sourceData = audioBuffer.getChannelData(0); // Берем первый канал (моно)
    
    for (let i = 0; i < targetLength; i++) {
      const sourceIndex = i * sourceSampleRate / targetSampleRate;
      const index0 = Math.floor(sourceIndex);
      const index1 = Math.min(index0 + 1, sourceLength - 1);
      const fraction = sourceIndex - index0;
      
      resampled[i] = sourceData[index0] * (1 - fraction) + sourceData[index1] * fraction;
    }
    
    return resampled;
  };

  return (
    <div className="flex flex-col items-center gap-4">
      <button
        onClick={isRecording ? stopRecording : startRecording}
        disabled={isProcessing}
        className={`p-6 rounded-full transition-all ${
          isRecording 
            ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
            : 'bg-blue-500 hover:bg-blue-600'
        } ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        {isProcessing ? (
          <Loader2 className="w-8 h-8 text-white animate-spin" />
        ) : isRecording ? (
          <MicOff className="w-8 h-8 text-white" />
        ) : (
          <Mic className="w-8 h-8 text-white" />
        )}
      </button>
      
      <div className="text-center">
        <p className="text-sm font-medium text-gray-700">
          {isProcessing ? 'Обработка...' : isRecording ? 'Запись...' : 'Нажмите для записи'}
        </p>
        {isRecording && (
          <p className="text-xs text-gray-500 mt-1">
            Записывайте звук 2-3 раза для лучшего распознавания
          </p>
        )}
      </div>
    </div>
  );
}
