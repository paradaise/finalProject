# 🛠️ Исправление .env файлов

## 🚨 **ПРОБЛЕМЫ:**
1. Frontend не может подключиться (Failed to fetch)
2. Raspberry Pi использует HTTPS вместо HTTP
3. Интервалы не работают из-за SSL

## ✅ **РЕШЕНИЕ:**

### **На Windows (создать frontend/.env):**
```bash
cd frontend
echo VITE_API_HOST=192.168.0.94 > .env
echo VITE_API_PORT=8000 >> .env
echo VITE_USE_SSL=false >> .env
echo VITE_THEME=auto >> .env
echo VITE_LANGUAGE=ru >> .env
```

### **На Raspberry Pi (исправить .env):**
```bash
cd raspberry_pi
# Заменить USE_SSL=true на USE_SSL=false
sed -i 's/USE_SSL=true/USE_SSL=false/' .env

# Или вручную отредактировать:
nano .env
# Изменить: USE_SSL=false
```

## 🔄 **ПЕРЕЗАПУСК:**

1. **Backend:** `python main.py`
2. **Frontend:** `npm run dev` (создать .env сначала!)
3. **Raspberry Pi:** `python audio_client.py`

## ✅ **ПРОВЕРКА:**

После исправления должно быть:
- Frontend: http://192.168.0.94:8000
- Raspberry Pi: http://192.168.0.94:8000  
- Интервалы: 5с для уровня, 30с для детекции

**Теперь всё должно работать!** 🎉
