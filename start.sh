#!/bin/bash
# Quick Start Script cho Telegram Bot

echo "🚀 TELEGRAM BOT QUICK START"
echo "============================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 chưa được cài đặt!"
    echo "Cài đặt: sudo apt install python3 python3-pip"
    exit 1
fi

echo "✅ Python đã cài: $(python3 --version)"

# Tạo virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Tạo virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Cài dependencies
echo "📥 Cài đặt dependencies..."
pip install -r requirements.txt

# Check .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  File .env chưa tồn tại!"
    echo "Tạo file .env từ template..."
    cp .env.example .env
    echo ""
    echo "🔧 VUI LÒNG CẬP NHẬT FILE .env VỚI TELEGRAM TOKEN CỦA BẠN!"
    echo "Mở file .env và thay đổi TELEGRAM_BOT_TOKEN"
    echo ""
    read -p "Nhấn Enter sau khi đã cập nhật .env..."
fi

# Check TOKEN
source .env
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_bot_token_here" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN chưa được set trong file .env!"
    echo "Vui lòng cập nhật TOKEN từ @BotFather"
    exit 1
fi

echo ""
echo "✅ Cấu hình hoàn tất!"
echo ""
echo "🤖 Khởi động bot..."
echo "Nhấn Ctrl+C để dừng"
echo ""

# Run bot
python telegram_bot_with_reminder.py
