# 🔒 Возвращаем SSL (самоподписанные сертификаты)

## ✅ **ПРАВИЛЬНАЯ КОНФИГУРАЦИЯ ДЛЯ HTTPS:**

### **Frontend (.env):**
```bash
cd frontend
echo VITE_API_HOST=192.168.0.94 > .env
echo VITE_API_PORT=8000 >> .env
echo VITE_USE_SSL=true >> .env
echo VITE_THEME=auto >> .env
echo VITE_LANGUAGE=ru >> .env
```

### **Raspberry Pi (.env):**
```bash
cd raspberry_pi
# Убедиться что USE_SSL=true
sed -i 's/USE_SSL=false/USE_SSL=true/' .env
# или вручную: USE_SSL=true
```

### **Backend (.env):**
```bash
cd backend
# Проверить что SSL включен
cat .env | grep SSL
# Должно быть:
# USE_SSL=true
# SSL_CERT_PATH=certs/cert.pem
# SSL_KEY_PATH=certs/key.pem
```

## 🔐 **ПРОВЕРКА СЕРТИФИКАТОВ:**

Убедитесь что файлы существуют:
```bash
ls -la backend/certs/
# Должны быть:
# cert.pem
# key.pem
```

## 🚀 **ЗАПУСК С SSL:**

1. **Backend:** `python main.py`
   - Должен показать: `https://0.0.0.0:8000`
   
2. **Frontend:** `npm run dev`
   - Будет подключаться к: `https://192.168.0.94:8000`
   
3. **Raspberry Pi:** `python audio_client.py`
   - Будет отправлять на: `https://192.168.0.94:8000`

## ⚠️ **ЕСЛИ ОШИБКИ SSL:**

**В браузере:**
- Перейдите в `https://192.168.0.94:8000/health`
- Примите самоподписанный сертификат
- Нажмите "Дополнительно" → "Перейти на сайт"

**В Raspberry Pi:**
- SSL уже отключен в коде: `self.session.verify = False`
- Ошибок сертификата быть не должно

**Готово! Возвращаемся на HTTPS!** 🔒
