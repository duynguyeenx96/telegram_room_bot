# 🚀 HƯỚNG DẪN DEPLOY BOT TELEGRAM 24/7 VỚI NHẮC NHỞ TỰ ĐỘNG

## ⭐ Tính năng mới

✅ **Nhắc nhở tự động hàng tháng**
- Bot tự động gửi thông báo vào ngày bạn cài đặt
- Nhắc tính tiền đúng giờ, không bao giờ quên
- Chạy 24/7 trên server

## 📋 Chuẩn bị

### 1. Tạo Bot Telegram
```
1. Mở Telegram → tìm @BotFather
2. Gửi: /newbot
3. Đặt tên: "Quản lý phòng trọ"
4. Đặt username: "phongtro_calculator_bot"
5. Lưu TOKEN
```

### 2. Cài đặt Dependencies
```bash
pip install python-telegram-bot==20.7 python-dotenv
```

### 3. Tạo file .env
```bash
# Tạo file .env
nano .env
```

Nội dung file .env:
```
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ROOM_PRICE=3000000
ELECTRIC_PRICE=3500
WATER_PRICE=20000
INTERNET_PRICE=100000
PARKING_PRICE=50000
```

## 🎯 Cách sử dụng Nhắc nhở

### Cài đặt nhắc nhở
```
Trên Telegram:
1. Gửi: /nhacnho
2. Chọn ngày (1-28)
   VD: Chọn "1" = mỗi đầu tháng
3. Chọn giờ
   VD: Chọn "09:00" = 9 giờ sáng
4. Xong!
```

**Bot sẽ tự động:**
- Gửi tin nhắn nhắc nhở vào ngày 1 hàng tháng lúc 9:00 sáng
- Liệt kê các phòng cần tính tiền
- Nhắc bạn dùng /tinh để bắt đầu

### Quản lý nhắc nhở
```
/xemnhacnho - Xem lịch nhắc hiện tại
/tatnhacnho - Tắt nhắc nhở
/nhacnho    - Cài lại/Thay đổi lịch
```

## 🖥️ DEPLOY LÊN SERVER 24/7

Bot cần chạy liên tục để gửi nhắc nhở đúng giờ. Dưới đây là các cách deploy:

---

## ✅ CÁCH 1: VPS/Server Linux (Khuyên dùng)

### A. Dùng systemd (Tự động khởi động)

**Bước 1:** Upload code lên server
```bash
# Trên máy local
scp -r telegram_bot_with_reminder.py user@your-server:/home/user/bot/

# SSH vào server
ssh user@your-server
cd /home/user/bot/
```

**Bước 2:** Tạo service file
```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

Nội dung:
```ini
[Unit]
Description=Telegram Room Rental Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/bot
Environment="PATH=/home/your_username/bot/venv/bin"
ExecStart=/home/your_username/bot/venv/bin/python telegram_bot_with_reminder.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Bước 3:** Kích hoạt service
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start
sudo systemctl enable telegram-bot

# Start bot
sudo systemctl start telegram-bot

# Check status
sudo systemctl status telegram-bot

# Xem log
sudo journalctl -u telegram-bot -f
```

**Lệnh quản lý:**
```bash
sudo systemctl start telegram-bot    # Bật
sudo systemctl stop telegram-bot     # Tắt
sudo systemctl restart telegram-bot  # Restart
sudo systemctl status telegram-bot   # Xem trạng thái
```

---

### B. Dùng screen (Đơn giản hơn)

```bash
# Cài screen
sudo apt install screen

# Tạo session
screen -S telegram_bot

# Chạy bot
python telegram_bot_with_reminder.py

# Nhấn: Ctrl+A rồi D để thoát (bot vẫn chạy)

# Quay lại xem:
screen -r telegram_bot

# List tất cả session:
screen -ls

# Kill session:
screen -X -S telegram_bot quit
```

---

## ✅ CÁCH 2: Heroku (Miễn phí - Có giới hạn)

**Bước 1:** Tạo các file cần thiết

`Procfile`:
```
worker: python telegram_bot_with_reminder.py
```

`runtime.txt`:
```
python-3.11.0
```

**Bước 2:** Deploy
```bash
# Login Heroku
heroku login

# Tạo app
heroku create your-bot-name

# Set biến môi trường
heroku config:set TELEGRAM_BOT_TOKEN=your_token

# Deploy
git init
git add .
git commit -m "Initial commit"
git push heroku main

# Scale worker
heroku ps:scale worker=1

# Xem log
heroku logs --tail
```

**⚠️ Lưu ý:** Heroku free tier ngủ sau 30 phút không hoạt động. Nhắc nhở có thể bị delay.

---

## ✅ CÁCH 3: PythonAnywhere (Miễn phí)

**Bước 1:** Đăng ký tại https://www.pythonanywhere.com

**Bước 2:** Upload code
- Files → Upload: telegram_bot_with_reminder.py
- Tạo file .env với TOKEN

**Bước 3:** Tạo Always-on Task
- Tasks → Create always-on task
- Command: `python3 /home/yourusername/telegram_bot_with_reminder.py`

**⚠️ Lưu ý:** Free plan không có always-on. Cần nâng cấp $5/tháng.

---

## ✅ CÁCH 4: Oracle Cloud (Miễn phí vĩnh viễn)

Oracle Cloud cung cấp VPS miễn phí vĩnh viễn!

**Bước 1:** Đăng ký Oracle Cloud Free Tier
- https://www.oracle.com/cloud/free/
- Tạo VM instance (Ubuntu 22.04)

**Bước 2:** Setup server
```bash
# Update
sudo apt update && sudo apt upgrade -y

# Cài Python
sudo apt install python3-pip python3-venv -y

# Tạo thư mục
mkdir ~/telegram-bot
cd ~/telegram-bot

# Upload code (dùng SCP hoặc git)
```

**Bước 3:** Dùng systemd như CÁCH 1-A

---

## ✅ CÁCH 5: Raspberry Pi tại nhà

Nếu có Raspberry Pi:

```bash
# Setup như VPS
# Dùng systemd (CÁCH 1-A)
# Giữ Pi luôn bật nguồn
# Kết nối internet ổn định
```

---

## 🔧 Troubleshooting

### Bot không gửi nhắc nhở?

**1. Check log:**
```bash
# Nếu dùng systemd:
sudo journalctl -u telegram-bot -n 50

# Nếu dùng screen:
screen -r telegram_bot
```

**2. Kiểm tra timezone server:**
```bash
# Xem timezone
timedatectl

# Đổi timezone (VD: Việt Nam)
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
```

**3. Test nhắc nhở:**
```python
# Sửa giờ nhắc nhở thành 1-2 phút sau để test
# Sau khi test xong, đổi lại giờ thật
```

### Bot bị tắt khi đóng terminal?

```bash
# Phải dùng screen hoặc systemd
# KHÔNG chạy trực tiếp: python bot.py
```

### Lỗi "Job queue not available"?

```bash
# Cài thêm:
pip install python-telegram-bot[job-queue]
```

---

## 📊 Monitor Bot

### Check bot đang chạy:
```bash
# Dùng systemd:
sudo systemctl status telegram-bot

# Dùng screen:
screen -ls

# Check process:
ps aux | grep telegram
```

### Xem log realtime:
```bash
# systemd:
sudo journalctl -u telegram-bot -f

# File log (nếu có):
tail -f bot.log
```

---

## 🔐 Bảo mật

1. **Không commit .env lên Git:**
```bash
echo ".env" >> .gitignore
echo "room_data.json" >> .gitignore
```

2. **Chỉ cho phép user cụ thể:**
```python
# Thêm vào bot:
ALLOWED_USERS = [123456789, 987654321]  # Telegram user IDs

async def start(update, context):
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("Unauthorized!")
        return
    # ... code bình thường
```

3. **Backup dữ liệu:**
```bash
# Cron job backup mỗi ngày
crontab -e

# Thêm dòng:
0 2 * * * cp /home/user/bot/room_data.json /home/user/backups/room_data_$(date +\%Y\%m\%d).json
```

---

## 💡 Tips

1. **Ngày nhắc nhở nên chọn:**
   - Ngày 1-5: Đầu tháng, có thời gian thu tiền
   - Ngày 25-28: Cuối tháng, nhắc trước

2. **Giờ nhắc nhở nên chọn:**
   - 7:00-9:00: Sáng sớm, check trước khi đi làm
   - 18:00-20:00: Chiều tối, rảnh hơn

3. **Backup thường xuyên:**
   - Dùng /export để tải dữ liệu về
   - Lưu file .json vào Google Drive

---

## 🎉 Hoàn tất!

Bot giờ đã:
✅ Chạy 24/7
✅ Tự động nhắc nhở đúng giờ
✅ Không bao giờ quên tính tiền
✅ Tự động khởi động khi server restart

**Test ngay:**
1. Gửi `/nhacnho` trên Telegram
2. Chọn ngày và giờ (test với 1-2 phút sau)
3. Đợi nhận thông báo
4. Thành công! 🎊
