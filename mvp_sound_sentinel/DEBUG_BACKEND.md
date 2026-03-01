# 🔍 Отладка Backend SSL

## 📋 **Что сделать:**

1. **Перезапусти backend:**
```bash
cd backend
python main.py
```

2. **Ищи в логах:**
```
🔧 DEBUG: USE_SSL=true
🔧 DEBUG: USE_SSL parsed=True
```

3. **Если видишь False, значит .env не читается:**
```bash
# Проверь что .env в правильной папке:
cd backend
ls -la .env

# Проверь содержимое:
cat .env | grep USE_SSL
```

## 🚨 **Если USE_SSL=false:**

Добавь в начало main.py:
```python
import os
from dotenv import load_dotenv

# Явная загрузка .env
load_dotenv()

print(f"🔧 RAW USE_SSL: {os.getenv('USE_SSL')}")
```

**Запусти и проверь что появится!** 🔍
