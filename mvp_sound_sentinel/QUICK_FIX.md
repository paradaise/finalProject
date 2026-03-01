# 🚨 БЫСТРОЕ ИСПРАВЛЕНИЕ ВСЕХ ПРОБЛЕМ

## ❌ **ПРОБЛЕМЫ:**
1. Backend запускается на HTTP вместо HTTPS
2. Raspberry Pi отправляет каждые 0.2с вместо 5с
3. Frontend не может подключиться

## ✅ **РЕШЕНИЕ:**

### **1. Исправить backend/.env:**
```bash
cd backend
# Проверить что USE_SSL=true
cat .env | grep USE_SSL
# Если нет, добавить:
echo USE_SSL=true >> .env
```

### **2. Исправить raspberry_pi/.env:**
```bash
cd raspberry_pi
# Обновить интервалы
sed -i 's/AUDIO_LEVEL_UPDATE_INTERVAL=0.5/AUDIO_LEVEL_UPDATE_INTERVAL=5/' .env
sed -i 's/DETECTION_INTERVAL=2.0/DETECTION_INTERVAL=30/' .env
# Проверить:
cat .env | grep -E "(AUDIO_LEVEL_UPDATE_INTERVAL|DETECTION_INTERVAL)"
```

### **3. Создать frontend/.env:**
```bash
cd frontend
echo VITE_API_HOST=192.168.0.94 > .env
echo VITE_API_PORT=8000 >> .env
echo VITE_USE_SSL=true >> .env
```

### **4. Перезапустить всё:**
```bash
# Backend
cd backend && python main.py

# Frontend  
cd frontend && npm run dev

# Raspberry Pi
cd raspberry_pi && python audio_client.py
```

## 🔍 **ПРОВЕРКА:**

**Backend должен показать:**
```
📡 Сервер будет доступен на https://0.0.0.0:8000
```

**Raspberry Pi должен показать:**
```
📡 Уровень звука каждые 5.0с
🕐 Детекция каждые 30.0с
```

**Frontend должен подключиться без ошибок!**

**Сделать по шагам и проверить каждый!** 🎯
