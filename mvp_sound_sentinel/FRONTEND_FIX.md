# 🛠️ Исправление Frontend

## ❌ **Проблема:** Failed to fetch + WebSocket error

## ✅ **Решение:**

### **1. Проверь текущий .env:**
```bash
cd frontend
cat .env
```

### **2. Создай правильный .env:**
```bash
cd frontend
echo VITE_API_HOST=192.168.0.94 > .env
echo VITE_API_PORT=8000 >> .env
echo VITE_USE_SSL=true >> .env
echo VITE_THEME=auto >> .env
echo VITE_LANGUAGE=ru >> .env
```

### **3. Проверь что создалось:**
```bash
cat .env
# Должно быть:
# VITE_API_HOST=192.168.0.94
# VITE_API_PORT=8000
# VITE_USE_SSL=true
```

### **4. Перезапусти frontend:**
```bash
npm run dev
```

### **5. Проверь в консоли браузера:**
- Должно быть запросы к `https://192.168.0.94:8000`
- WebSocket к `wss://192.168.0.94:8000/ws`

## 🔍 **Если все еще ошибка:**

Открой в браузере `https://192.168.0.94:8000/health`
- Если ошибка сертификата - нажми "Дополнительно" → "Перейти"
- После этого frontend сможет подключаться

**Готово! Frontend должен заработать!** 🎉
