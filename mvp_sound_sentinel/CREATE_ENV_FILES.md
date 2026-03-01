# 🚀 Быстрое создание .env файлов

## 📋 Скопируйте эти команды в терминал:

### Frontend (Windows):
```bash
cd frontend
echo VITE_API_HOST=192.168.0.94 > .env
echo VITE_API_PORT=8000 >> .env
echo VITE_USE_SSL=false >> .env
echo VITE_THEME=auto >> .env
echo VITE_LANGUAGE=ru >> .env
```

### Raspberry Pi (Linux):
```bash
cd raspberry_pi
echo SERVER_HOST=192.168.0.94 > .env
echo SERVER_PORT=8000 >> .env
echo USE_SSL=false >> .env
echo DEVICE_NAME="Raspberry Pi Monitor" >> .env
echo DETECTION_INTERVAL=2.0 >> .env
echo AUDIO_LEVEL_UPDATE_INTERVAL=0.5 >> .env
```

## ✅ Проверка:

После создания файлов проверьте:
```bash
# Frontend
cat frontend/.env

# Raspberry Pi  
cat raspberry_pi/.env
```

## 🔄 Перезапустите:

1. Backend: `python main.py`
2. Frontend: `npm run dev` 
3. Raspberry Pi: `python audio_client.py`

**Готово! Ошибки 405 и Failed to fetch должны исчезнуть!** 🎉
