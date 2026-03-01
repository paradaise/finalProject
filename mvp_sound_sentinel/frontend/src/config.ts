/**
 * Конфигурация Sound Sentinel Frontend
 */

interface Config {
  // API сервер
  API_BASE_URL: string;
  WS_URL: string;
  
  // UI настройки
  THEME: 'light' | 'dark' | 'auto';
  LANGUAGE: 'ru' | 'en';
  
  // График аудио уровня
  AUDIO_CHART_UPDATE_INTERVAL: number; // мс
  AUDIO_CHART_MAX_POINTS: number;
  
  // Уведомления
  NOTIFICATION_AUTO_HIDE_DELAY: number; // мс
  MAX_NOTIFICATIONS: number;
  
  // Детекции
  DETECTIONS_REFRESH_INTERVAL: number; // мс
  MAX_DETECTIONS_DISPLAY: number;
  
  // WebSocket
  WS_RECONNECT_DELAY: number; // мс
  WS_MAX_RECONNECT_ATTEMPTS: number;
  
  // Отладка
  DEBUG: boolean;
  VERBOSE_LOGGING: boolean;
}

// Получаем конфигурацию из переменных окружения или используем значения по умолчанию
const getEnvConfig = (): Partial<Config> => {
  // API URL из переменной окружения или по умолчанию
  const apiHost = import.meta.env.VITE_API_HOST || '192.168.0.61';
  const apiPort = import.meta.env.VITE_API_PORT || '8000';
  const useSSL = import.meta.env.VITE_USE_SSL !== 'false';
  
  return {
    API_BASE_URL: `${useSSL ? 'https' : 'http'}://${apiHost}:${apiPort}`,
    WS_URL: `${useSSL ? 'wss' : 'ws'}://${apiHost}:${apiPort}/ws`,
    
    THEME: (import.meta.env.VITE_THEME as 'light' | 'dark' | 'auto') || 'auto',
    LANGUAGE: (import.meta.env.VITE_LANGUAGE as 'ru' | 'en') || 'ru',
    
    AUDIO_CHART_UPDATE_INTERVAL: parseInt(import.meta.env.VITE_AUDIO_CHART_UPDATE_INTERVAL || '100'),
    AUDIO_CHART_MAX_POINTS: parseInt(import.meta.env.VITE_AUDIO_CHART_MAX_POINTS || '100'),
    
    NOTIFICATION_AUTO_HIDE_DELAY: parseInt(import.meta.env.VITE_NOTIFICATION_AUTO_HIDE_DELAY || '5000'),
    MAX_NOTIFICATIONS: parseInt(import.meta.env.VITE_MAX_NOTIFICATIONS || '10'),
    
    DETECTIONS_REFRESH_INTERVAL: parseInt(import.meta.env.VITE_DETECTIONS_REFRESH_INTERVAL || '1000'),
    MAX_DETECTIONS_DISPLAY: parseInt(import.meta.env.VITE_MAX_DETECTIONS_DISPLAY || '50'),
    
    WS_RECONNECT_DELAY: parseInt(import.meta.env.VITE_WS_RECONNECT_DELAY || '3000'),
    WS_MAX_RECONNECT_ATTEMPTS: parseInt(import.meta.env.VITE_WS_MAX_RECONNECT_ATTEMPTS || '10'),
    
    DEBUG: import.meta.env.VITE_DEBUG === 'true',
    VERBOSE_LOGGING: import.meta.env.VITE_VERBOSE_LOGGING === 'true',
  };
};

// Итоговая конфигурация
export const config: Config = {
  ...getEnvConfig(),
} as Config;

// Экспорт для использования в компонентах
export default config;
