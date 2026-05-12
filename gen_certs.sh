#!/bin/bash
# scripts/gen_certs.sh — Генерация самоподписанного SSL-сертификата
# Использование: bash scripts/gen_certs.sh [IP-адрес сервера]

set -e

IP="${1:-192.168.0.61}"
CERTS_DIR="./mvp_sound_sentinel/backend/certs"

echo "🔐 Генерация SSL сертификата для IP: $IP"
mkdir -p "$CERTS_DIR"

openssl req -x509 -newkey rsa:4096 \
  -keyout "$CERTS_DIR/key.pem" \
  -out    "$CERTS_DIR/cert.pem" \
  -days   365 \
  -nodes \
  -subj   "/CN=$IP" \
  -addext "subjectAltName=IP:$IP,IP:127.0.0.1,DNS:localhost"

echo "✅ Сертификат создан:"
echo "   Ключ:        $CERTS_DIR/key.pem"
echo "   Сертификат:  $CERTS_DIR/cert.pem"
echo ""
echo "⚠️  Это самоподписанный сертификат."
echo "   В браузере нужно вручную добавить исключение:"
echo "   Откройте https://$IP:8000 → 'Дополнительно' → 'Перейти на сайт'"
