const API_BASE_URL = 'http://192.168.0.61:8000';

export interface Device {
  id: string;
  name: string;
  ip_address: string;
  mac_address: string;
  model: string;
  model_image_url?: string;
  microphone_info?: string;
  wifi_signal: number;
  status: string;
  last_seen: string;
  created_at: string;
}

export interface SoundDetection {
  id: string;
  device_id: string;
  sound_type: string;
  confidence: number;
  timestamp: string;
  mfcc_features?: number[];
}

export interface CustomSound {
  id: string;
  name: string;
  sound_type: 'excluded' | 'specific';
  mfcc_features: number[];
  device_id: string;
  created_at: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request(endpoint: string, options: RequestInit = {}): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Устройства
  async getDevices(): Promise<Device[]> {
    return this.request('/devices');
  }

  // Детекции звуков
  async getDetections(deviceId: string, limit: number = 50): Promise<SoundDetection[]> {
    return this.request(`/detections/${deviceId}?limit=${limit}`);
  }

  // Пользовательские звуки
  async getCustomSounds(): Promise<CustomSound[]> {
    return this.request('/custom_sounds');
  }

  async addCustomSound(name: string, soundType: 'excluded' | 'specific', mfccFeatures: number[], deviceId: string): Promise<CustomSound> {
    return this.request('/custom_sounds', {
      method: 'POST',
      body: JSON.stringify({
        name,
        sound_type: soundType,
        mfcc_features: mfccFeatures,
        device_id: deviceId,
      }),
    });
  }

  async deleteCustomSound(soundId: string): Promise<void> {
    return this.request(`/custom_sounds/${soundId}`, {
      method: 'DELETE',
    });
  }

  // Удаление устройства
  async deleteDevice(deviceId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/devices/${deviceId}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Failed to delete device');
    }
  }

  // Получение детекций для устройства
  async getDeviceEvents(deviceId: string, limit: number = 50): Promise<SoundDetection[]> {
    return this.request(`/detections/${deviceId}?limit=${limit}`);
  }

  // WebSocket для реального времени
  connectWebSocket(onMessage: (data: any) => void): WebSocket {
    const ws = new WebSocket(`${this.baseUrl.replace('http', 'ws')}/ws`);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('WebSocket message error:', error);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Автоматическое переподключение через 5 секунд
      setTimeout(() => {
        this.connectWebSocket(onMessage);
      }, 5000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    return ws;
  }

  // Проверка здоровья API
  async healthCheck(): Promise<any> {
    return this.request('/health');
  }
}

export const apiClient = new ApiClient();
