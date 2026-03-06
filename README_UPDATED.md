# 🏠 Telegram Bot Quản Lý Tiền Thuê Phòng - Auto Reminder

Bot Telegram **tự động nhắc nhở** và tính tiền thuê phòng trọ hàng tháng, bao gồm điện, nước, internet và các khoản phí khác.

## ✨ Tính năng

### 🔔 Nhắc nhở tự động (MỚI!)
- ⏰ Tự động gửi thông báo vào ngày bạn cài đặt mỗi tháng
- 📅 Tùy chỉnh ngày (1-28) và giờ nhắc nhở
- 🏠 Tự động liệt kê phòng cần tính tiền
- 🔄 Chạy 24/7 không bao giờ quên

### 💰 Tính toán thông minh
- ⚡ Tính tiền điện theo số đo (kWh)
- 💧 Tính tiền nước theo số đo (m³)
- 🏠 Quản lý nhiều phòng cùng lúc
- 📊 Lưu lịch sử thanh toán
- 🧾 Tạo hóa đơn chi tiết đẹp mắt
- 💡 Tự động nhớ số cũ cho tháng sau

## 🚀 Quick Start (5 phút)

### 1. Tạo Bot Telegram
```bash
# Mở Telegram → tìm @BotFather
# Gửi: /newbot
# Làm theo hướng dẫn và LƯU TOKEN
```

### 2. Cài đặt và chạy
```bash
# Clone hoặc download code
cd telegram-bot

# Chạy script tự động
chmod +x start.sh
./start.sh
```

Script sẽ tự động:
- ✅ Kiểm tra Python
- ✅ Tạo virtual environment
- ✅ Cài dependencies
- ✅ Tạo file .env từ template
- ✅ Khởi động bot

### 3. Cấu hình (chỉnh file .env)
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ROOM_PRICE=3000000
ELECTRIC_PRICE=3500
WATER_PRICE=20000
INTERNET_PRICE=100000
PARKING_PRICE=50000
```

### 4. Test thử
```
Trên Telegram:
1. Tìm bot của bạn
2. Gửi: /start
3. Gửi: /nhacnho
4. Cài đặt nhắc nhở
5. Đợi nhận thông báo!
```

## 📱 Hướng dẫn sử dụng

### Lệnh cơ bản

| Lệnh | Mô tả |
|------|-------|
| `/start` | Bắt đầu và xem menu |
| `/tinh` | Tính tiền phòng |
| `/nhacnho` | Cài đặt nhắc nhở tự động ⭐ |
| `/xemnhacnho` | Xem lịch nhắc hiện tại |
| `/tatnhacnho` | Tắt nhắc nhở |
| `/lichsu` | Xem lịch sử thanh toán |
| `/gia` | Xem bảng giá |
| `/capnhatgia` | Cập nhật giá |
| `/export` | Xuất dữ liệu backup |
| `/help` | Hướng dẫn chi tiết |

### 🔔 Cài đặt nhắc nhở

**Bước 1:** Gửi `/nhacnho`

**Bước 2:** Chọn ngày (1-28)
- Ví dụ: Chọn **1** = Mỗi đầu tháng
- Khuyên dùng ngày 1-5 để có thời gian thu tiền

**Bước 3:** Chọn giờ
- Ví dụ: **09:00** = 9 giờ sáng
- Hoặc tự nhập: 07:30, 14:00, 20:15...

**Kết quả:** Bot sẽ tự động gửi tin nhắn nhắc nhở vào:
- 📅 Ngày 1 hàng tháng
- ⏰ Lúc 9:00 sáng
- 🏠 Liệt kê tất cả phòng cần tính

### 💰 Quy trình tính tiền

```
User: /tinh
Bot: Nhập tên phòng?

User: Phòng 101
Bot: Số điện cũ? (có gợi ý số tháng trước)

User: 1250
Bot: Số điện mới?

User: 1380
Bot: Số nước cũ?

User: 45
Bot: Số nước mới?

User: 52
Bot: 🧾 [Hiển thị hóa đơn chi tiết]
     Xác nhận lưu? (Có/Không)

User: Có
Bot: ✅ Đã lưu!
```

### 📊 Hóa đơn tự động

```
🧾 HÓA ĐƠN TIỀN PHÒNG
━━━━━━━━━━━━━━━━━━━━

🏠 Phòng: Phòng 101
📅 Tháng: 03/2025

━━━━━━━━━━━━━━━━━━━━

💰 CHI TIẾT:

🏠 Tiền phòng: 3,000,000 VNĐ

⚡ Tiền điện:
   • Cũ: 1250.0 → Mới: 1380.0
   • Tiêu thụ: 130.0 kWh × 3,500đ
   • Thành tiền: 455,000 VNĐ

💧 Tiền nước:
   • Cũ: 45.0 → Mới: 52.0
   • Tiêu thụ: 7.0 m³ × 20,000đ
   • Thành tiền: 140,000 VNĐ

📡 Internet: 100,000 VNĐ
🏍️ Gửi xe: 50,000 VNĐ

━━━━━━━━━━━━━━━━━━━━
💵 TỔNG CỘNG: 3,745,000 VNĐ
━━━━━━━━━━━━━━━━━━━━
```

## 🖥️ Deploy lên Server 24/7

Bot cần chạy 24/7 để gửi nhắc nhở đúng giờ. Xem file `DEPLOYMENT_GUIDE.md` để biết chi tiết!

### Quick Deploy Options:

#### ✅ VPS/Server (Khuyên dùng)
```bash
# Dùng systemd
sudo cp telegram-bot.service /etc/systemd/system/
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

#### ✅ Oracle Cloud (Miễn phí vĩnh viễn)
- Free tier VPS
- Dùng systemd như trên
- Chi tiết trong DEPLOYMENT_GUIDE.md

#### ✅ Screen (Đơn giản)
```bash
screen -S telegram_bot
python telegram_bot_with_reminder.py
# Nhấn Ctrl+A+D để thoát
```

## 📂 Cấu trúc File

```
telegram-bot/
├── telegram_bot_with_reminder.py  # Bot chính với tính năng nhắc nhở
├── telegram_room_bot.py           # Version cơ bản (không có reminder)
├── requirements.txt               # Dependencies
├── .env.example                   # Template cấu hình
├── .env                           # Cấu hình thực (tự tạo)
├── .gitignore                     # Git ignore
├── start.sh                       # Script khởi động tự động
├── telegram-bot.service           # Systemd service file
├── README.md                      # File này
├── DEPLOYMENT_GUIDE.md            # Hướng dẫn deploy chi tiết
└── room_data.json                 # Database (tự động tạo)
```

## 💾 Dữ liệu

Tất cả dữ liệu lưu trong `room_data.json`:

```json
{
  "rooms": {
    "Phòng 101": {
      "history": [...]
    }
  },
  "prices": {...},
  "reminders": {
    "123456789": {
      "day": 1,
      "time": "09:00",
      "rooms": ["Phòng 101"],
      "enabled": true
    }
  }
}
```

**⚠️ QUAN TRỌNG: Backup file này thường xuyên!**

## 🔧 Troubleshooting

### Bot không gửi nhắc nhở?

**1. Kiểm tra bot có đang chạy:**
```bash
# Nếu dùng systemd:
sudo systemctl status telegram-bot

# Nếu dùng screen:
screen -ls
```

**2. Kiểm tra timezone server:**
```bash
timedatectl
# Đổi timezone nếu sai:
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
```

**3. Kiểm tra log:**
```bash
sudo journalctl -u telegram-bot -n 50
```

### Bot bị tắt khi đóng terminal?

→ Dùng `screen` hoặc `systemd`, KHÔNG chạy trực tiếp `python bot.py`

### Muốn test nhắc nhở ngay?

→ Cài đặt giờ nhắc nhở là 1-2 phút sau để test

## 🔐 Bảo mật

### 1. Không commit secret lên Git
```bash
# .gitignore đã được setup sẵn
# Chứa: .env, room_data.json, *.pyc, etc.
```

### 2. Giới hạn user được dùng bot
```python
# Thêm vào đầu file bot:
ALLOWED_USERS = [123456789, 987654321]  # Telegram user IDs

# Trong mỗi handler:
if update.effective_user.id not in ALLOWED_USERS:
    return
```

### 3. Backup tự động
```bash
# Thêm vào crontab:
0 2 * * * cp /path/to/room_data.json /path/to/backup/$(date +\%Y\%m\%d).json
```

## 💡 Tips & Best Practices

### Ngày nhắc nhở nên chọn:
- **Ngày 1-5:** Đầu tháng, có thời gian thu tiền
- **Ngày 25-28:** Cuối tháng, nhắc trước

### Giờ nhắc nhở nên chọn:
- **7:00-9:00:** Sáng sớm
- **18:00-20:00:** Tối về nhà
- Tránh giờ ngủ (23:00-6:00)

### Quản lý nhiều phòng:
- Bot tự động track tất cả phòng
- Mỗi phòng có lịch sử riêng
- Nhắc nhở sẽ list tất cả phòng cần tính

### Backup thường xuyên:
- Dùng `/export` để tải về
- Lưu vào Google Drive
- Setup cron backup tự động

## 🎯 Roadmap

- [ ] Gửi hóa đơn qua email
- [ ] Export Excel
- [ ] Thống kê tiêu thụ điện nước
- [ ] Multi-language support
- [ ] Web dashboard
- [ ] Payment integration

## 📞 Support

Có vấn đề? 
- Đọc `DEPLOYMENT_GUIDE.md`
- Check Troubleshooting section
- Tạo issue trên GitHub

## 📝 License

MIT License - Dùng tự do!

---

Made with ❤️ for Vietnamese landlords

**Star ⭐ repo này nếu thấy hữu ích!**
