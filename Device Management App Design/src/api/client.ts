// API клиент для взаимодействия с Sound Sentinel API
const API_BASE_URL = 'http://192.168.0.61:8000';

export interface Device {
  id: string;
  name: string;
  ip_address: string;
  status: 'online' | 'offline' | 'error';
  last_seen: string;
  temperature?: number;
  cpu_load?: number;
}

export interface AudioEvent {
  id: string;
  sound_type: string;
  confidence: number;
  timestamp: string;
  device_id: string;
  intensity: number;
  description: string;
}

export interface CustomSound {
  id: string;
  name: string;
  sound_type: 'specific' | 'excluded';
  mfcc_features: number[];
  created_at: string;
  device_id: string;
}

// Типы для мобильного приложения (совместимость с существующими компонентами)
export interface ExcludedSound {
  id: string;
  name: string;
  icon: string;
  recordedAt: Date;
  duration: number;
}

export interface SpecificSound {
  id: string;
  name: string;
  icon: string;
  priority: 'low' | 'medium' | 'high';
  recordedAt: Date;
  duration: number;
}

class ApiClient {
  private baseUrl: string;
  private wsConnection: WebSocket | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  // Устройства
  async getDevices(): Promise<Device[]> {
    try {
      const response = await fetch(`${this.baseUrl}/devices`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Error fetching devices:", error);
      throw error;
    }
  }

  async registerDevice(
    device: Omit<Device, "id" | "last_seen">,
  ): Promise<Device> {
    try {
      const response = await fetch(`${this.baseUrl}/devices`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(device),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Error registering device:", error);
      throw error;
    }
  }

  // Аудио события
  async getDeviceEvents(
    deviceId: string,
    limit: number = 50,
  ): Promise<AudioEvent[]> {
    try {
      const response = await fetch(
        `${this.baseUrl}/events/${deviceId}?limit=${limit}`,
      );
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Error fetching device events:", error);
      throw error;
    }
  }

  // Пользовательские звуки
  async addCustomSound(
    name: string,
    soundType: "specific" | "excluded",
    mfccFeatures: number[],
    deviceId: string,
  ): Promise<{ status: string; sound_id: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/custom_sounds`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name,
          sound_type: soundType,
          mfcc_features: mfccFeatures,
          device_id: deviceId,
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Error adding custom sound:", error);
      throw error;
    }
  }

  async getCustomSounds(deviceId?: string): Promise<CustomSound[]> {
    try {
      const url = deviceId
        ? `${this.baseUrl}/custom_sounds?device_id=${deviceId}`
        : `${this.baseUrl}/custom_sounds`;

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Error fetching custom sounds:", error);
      throw error;
    }
  }

  async deleteCustomSound(soundId: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/custom_sounds/${soundId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error("Error deleting custom sound:", error);
      throw error;
    }
  }

  async deleteDevice(deviceId: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/devices/${deviceId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error("Error deleting device:", error);
      throw error;
    }
  }

  // WebSocket для реального времени
  connectWebSocket(onMessage: (data: AudioEvent) => void): void {
    try {
      this.wsConnection = new WebSocket(
        `${this.baseUrl.replace("http", "ws")}/ws`,
      );

      this.wsConnection.onopen = () => {
        console.log("WebSocket connected");
      };

      this.wsConnection.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };

      this.wsConnection.onclose = () => {
        console.log("WebSocket disconnected");
        // Автоматическое переподключение через 5 секунд
        setTimeout(() => {
          this.connectWebSocket(onMessage);
        }, 5000);
      };

      this.wsConnection.onerror = (error) => {
        console.error("WebSocket error:", error);
      };
    } catch (error) {
      console.error("Error connecting WebSocket:", error);
    }
  }

  disconnectWebSocket(): void {
    if (this.wsConnection) {
      this.wsConnection.close();
      this.wsConnection = null;
    }
  }

  // Вспомогательные функции
  async testConnection(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/`);
      return response.ok;
    } catch (error) {
      console.error("Connection test failed:", error);
      return false;
    }
  }

  // Извлечение MFCC из аудио (для записи пользовательских звуков)
  async extractMfccFromAudio(audioBlob: Blob): Promise<number[]> {
    // Это должна быть реализация на клиенте или через API
    // Для упрощения пока вернем заглушку
    try {
      const formData = new FormData();
      formData.append("audio", audioBlob);

      const response = await fetch(`${this.baseUrl}/extract_mfcc`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result.mfcc_features;
    } catch (error) {
      console.error("Error extracting MFCC:", error);
      throw error;
    }
  }
}

export const apiClient = new ApiClient();
export default apiClient;
