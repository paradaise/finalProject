// Для локальной сети с HTTPS - заменить на IP твоего ПК
// Узнать свой IP: ipconfig (Windows) или ifconfig (Mac/Linux)
const API_BASE_URL = 'https://192.168.0.61:8000'; // Замени на свой IP

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
  embeddings?: number[];
}

export interface CustomSound {
  id: string;
  name: string;
  sound_type: "specific" | "excluded";
  embeddings: number[];
  centroid: number[];
  threshold: number;
  device_id: string;
  created_at: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
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
    return this.request("/devices");
  }

  // Детекции звуков
  async getDetections(
    deviceId: string,
    limit: number = 50,
  ): Promise<SoundDetection[]> {
    return this.request(`/detections/${deviceId}?limit=${limit}`);
  }

  // Пользовательские звуки с YAMNet embeddings
  async getCustomSounds(): Promise<CustomSound[]> {
    return this.request("/custom_sounds");
  }

  async trainCustomSound(soundData: {
    name: string;
    sound_type: "specific" | "excluded";
    device_id: string;
    audio_recordings: number[][];
    threshold?: number;
  }): Promise<any> {
    return this.request("/custom_sounds/train", {
      method: "POST",
      body: JSON.stringify(soundData),
    });
  }

  async addCustomSound(
    name: string,
    soundType: "specific" | "excluded",
    embeddings: number[],
    deviceId: string,
    threshold?: number,
  ): Promise<CustomSound> {
    return this.request("/custom_sounds", {
      method: "POST",
      body: JSON.stringify({
        name,
        sound_type: soundType,
        embeddings,
        device_id: deviceId,
        threshold: threshold || 0.75,
      }),
    });
  }

  async deleteCustomSound(soundId: string): Promise<void> {
    return this.request(`/custom_sounds/${soundId}`, {
      method: "DELETE",
    });
  }

  // Удаление устройства
  async deleteDevice(deviceId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/devices/${deviceId}`, {
      method: "DELETE",
    });
    if (!response.ok) {
      throw new Error("Failed to delete device");
    }
  }

  // Получение детекций для устройства
  async getDeviceEvents(
    deviceId: string,
    limit: number = 1000,
  ): Promise<any[]> {
    const response = await this.request(
      `/detections/${deviceId}?limit=${limit}`,
    );
    // Возвращаем detections из нового формата
    return response.detections || response;
  }

  // WebSocket для реального времени
  connectWebSocket(onMessage: (data: any) => void): WebSocket {
    const ws = new WebSocket(`${this.baseUrl.replace("http", "ws")}/ws`);

    ws.onopen = () => {
      console.log("WebSocket connected");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error("WebSocket message error:", error);
      }
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
      // Автоматическое переподключение через 5 секунд
      setTimeout(() => {
        this.connectWebSocket(onMessage);
      }, 5000);
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    return ws;
  }

  // Проверка здоровья API
  async healthCheck(): Promise<any> {
    return this.request("/health");
  }

  // Получение всех звуков YAMNet
  async getYamnetSounds(): Promise<any> {
    return this.request("/yamnet_sounds");
  }

  // Настройки уведомлений
  async getNotificationSettings(deviceId: string): Promise<{
    notification_sounds: string[];
    excluded_sounds: string[];
    custom_sounds: { name: string; type: string }[];
  }> {
    return this.request(`/notification_settings/${deviceId}`);
  }

  async addNotificationSound(
    soundName: string,
    deviceId: string,
  ): Promise<any> {
    return this.request("/notification_sounds", {
      method: "POST",
      body: JSON.stringify({
        sound_name: soundName,
        device_id: deviceId,
      }),
    });
  }

  async addExcludedSound(soundName: string, deviceId: string): Promise<any> {
    return this.request("/excluded_sounds", {
      method: "POST",
      body: JSON.stringify({
        sound_name: soundName,
        device_id: deviceId,
      }),
    });
  }

  async deleteNotificationSound(soundId: string): Promise<any> {
    return this.request(`/notification_sounds/${soundId}`, {
      method: "DELETE",
    });
  }

  async deleteExcludedSound(soundId: string): Promise<any> {
    return this.request(`/excluded_sounds/${soundId}`, {
      method: "DELETE",
    });
  }
}

export const apiClient = new ApiClient();
