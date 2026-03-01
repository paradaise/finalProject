/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_HOST: string
  readonly VITE_API_PORT: string
  readonly VITE_USE_SSL: string
  readonly VITE_THEME: 'light' | 'dark' | 'auto'
  readonly VITE_LANGUAGE: 'ru' | 'en'
  readonly VITE_AUDIO_CHART_UPDATE_INTERVAL: string
  readonly VITE_AUDIO_CHART_MAX_POINTS: string
  readonly VITE_NOTIFICATION_AUTO_HIDE_DELAY: string
  readonly VITE_MAX_NOTIFICATIONS: string
  readonly VITE_DETECTIONS_REFRESH_INTERVAL: string
  readonly VITE_MAX_DETECTIONS_DISPLAY: string
  readonly VITE_WS_RECONNECT_DELAY: string
  readonly VITE_WS_MAX_RECONNECT_ATTEMPTS: string
  readonly VITE_DEBUG: string
  readonly VITE_VERBOSE_LOGGING: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
