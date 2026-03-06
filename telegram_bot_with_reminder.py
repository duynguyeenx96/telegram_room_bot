#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot tính tiền thuê phòng trọ - With Auto Monthly Reminder
"""

import json
import os
import io
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import psycopg2
from psycopg2.extras import Json
from datetime import datetime, time
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

DATABASE_URL = os.getenv('DATABASE_URL')
_conn = None


def get_conn():
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg2.connect(DATABASE_URL)
        _conn.autocommit = True
    return _conn


def init_db():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'bot_data' AND column_name = 'id'
              AND data_type = 'integer'
        """)
        if cur.fetchone():
            cur.execute("DROP TABLE bot_data")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bot_data (
                chat_id TEXT PRIMARY KEY,
                data JSONB NOT NULL
            )
        """)

# Các trạng thái trong conversation
ROOM_NAME, OLD_ELECTRIC, NEW_ELECTRIC, OLD_WATER, NEW_WATER, CONFIRM = range(6)
UPDATE_PRICE_TYPE, UPDATE_PRICE_VALUE = range(6, 8)
SET_REMINDER_DAY, SET_REMINDER_TIME = range(8, 10)
ADJUST_ROOM, ADJUST_TYPE, ADJUST_VALUE = range(10, 13)
ADD_FEE_NAME, ADD_FEE_PRICE, ADD_FEE_MULTIPLIER = range(13, 16)
SETTINGS_TYPE = 16

# Load từ .env nếu có
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Đã load .env file")
except ImportError:
    print("⚠️  python-dotenv chưa cài, dùng giá mặc định")

# Giá mặc định
DEFAULT_PRICES = {
    "room_price": int(os.getenv("ROOM_PRICE", 3000000)),
    "electric_price": int(os.getenv("ELECTRIC_PRICE", 3500)),
    "water_price": int(os.getenv("WATER_PRICE", 20000)),
    "internet": int(os.getenv("INTERNET_PRICE", 100000)),
    "parking": int(os.getenv("PARKING_PRICE", 50000)),
}

DEFAULT_SETTINGS = {
    "invoice_format": "full",
    "stats_format": "simple",
}


def load_data(chat_id: str):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT data FROM bot_data WHERE chat_id = %s", (chat_id,))
        row = cur.fetchone()
    if row:
        return row[0]
    return {
        'rooms': {},
        'prices': DEFAULT_PRICES.copy(),
        'custom_fees': {},
        'settings': DEFAULT_SETTINGS.copy(),
        'reminders': {}
    }


def save_data(chat_id: str, data):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO bot_data (chat_id, data) VALUES (%s, %s)
               ON CONFLICT (chat_id) DO UPDATE SET data = EXCLUDED.data""",
            (chat_id, Json(data))
        )


def load_all_reminders():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT chat_id, data FROM bot_data")
        rows = cur.fetchall()
    result = {}
    for chat_id, data in rows:
        for cid, reminder in data.get('reminders', {}).items():
            result[cid] = reminder
    return result


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler cho lệnh /start"""
    welcome_message = """
🏠 <b>Chào mừng đến với Bot Quản lý Phòng Trọ!</b>

📋 <b>Danh sách lệnh:</b>
/tinh - Tính tiền phòng tháng này
/lichsu - Xem lịch sử thanh toán
/gia - Xem bảng giá hiện tại
/capnhatgia - Cập nhật bảng giá
/suaso - Sửa số điện/nước cũ (nếu nhập nhầm)
/themphi - Thêm phí tùy chỉnh mới
/nhacnho - Cài đặt nhắc nhở hàng tháng ⏰
/xemnhacnho - Xem lịch nhắc nhở
/tatnhacnho - Tắt nhắc nhở
/caidat - Cài đặt kiểu hiển thị hóa đơn
/export - Xuất dữ liệu
/help - Hướng dẫn sử dụng

💡 <b>Tính năng mới:</b> Dùng /nhacnho để bot tự động nhắc bạn tính tiền mỗi tháng!
"""
    await update.message.reply_text(welcome_message, parse_mode='HTML')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler cho lệnh /help"""
    help_text = """
📖 <b>HƯỚNG DẪN SỬ DỤNG</b>

<b>1. Tính tiền phòng (/tinh):</b>
   - Nhập tên phòng (VD: Phòng 101)
   - Nhập số điện cũ và mới
   - Nhập số nước cũ và mới
   - Bot sẽ tự động tính toán

<b>2. Nhắc nhở tự động (/nhacnho):</b>
   - Chọn ngày trong tháng (1-28)
   - Chọn giờ nhắc nhở
   - Bot sẽ tự động gửi thông báo mỗi tháng
   - VD: Ngày 1 hàng tháng lúc 9:00 sáng

<b>3. Xem lịch sử (/lichsu):</b>
   - Xem các lần thanh toán trước
   - Theo dõi số điện nước tháng trước

<b>4. Cập nhật giá (/capnhatgia):</b>
   - Thay đổi giá điện, nước
   - Cập nhật tiền phòng, internet, xe

💡 <b>Mẹo:</b> 
- Bot tự động lưu số điện nước mới thành số cũ cho tháng sau
- Dùng /nhacnho để không bao giờ quên tính tiền!
- Bot chạy 24/7, nhắc đúng giờ bạn cài đặt
"""
    await update.message.reply_text(help_text, parse_mode='HTML')


async def show_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hiển thị bảng giá"""
    chat_id = str(update.effective_chat.id)
    data = load_data(chat_id)
    prices = data.get("prices", DEFAULT_PRICES)
    custom_fees = data.get("custom_fees", {})

    price_text = f"""
💵 <b>BẢNG GIÁ HIỆN TẠI</b>

🏠 Tiền phòng: {prices['room_price']:,} VNĐ
⚡ Giá điện: {prices['electric_price']:,} VNĐ/kWh
💧 Giá nước: {prices['water_price']:,} VNĐ/m³
📡 Internet: {prices['internet']:,} VNĐ
🏍️ Gửi xe: {prices['parking']:,} VNĐ
"""

    if custom_fees:
        price_text += "\n💰 <b>PHÍ KHÁC:</b>\n"
        for fee_name, fee_data in custom_fees.items():
            price_text += f"   • {fee_name}: {fee_data['price']:,}đ (hệ số: {fee_data['multiplier']})\n"

    price_text += "\nDùng /capnhatgia để thay đổi giá, /themphi để thêm phí mới"

    await update.message.reply_text(price_text, parse_mode='HTML')


async def set_reminder_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bắt đầu cài đặt nhắc nhở"""
    keyboard = [
        ['1', '5', '10', '15'],
        ['20', '25', '28', '❌ Hủy']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    
    await update.message.reply_text(
        "⏰ <b>CÀI ĐẶT NHẮC NHỞ HÀNG THÁNG</b>\n\n"
        "Chọn ngày trong tháng bạn muốn được nhắc nhở (1-28):\n\n"
        "💡 <i>Khuyên dùng ngày 1-5 đầu tháng để có thời gian thu tiền</i>",
        parse_mode='HTML',
        reply_markup=reply_markup
    )
    return SET_REMINDER_DAY


async def reminder_day_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nhận ngày nhắc nhở"""
    text = update.message.text
    
    if text == '❌ Hủy':
        await update.message.reply_text(
            "Đã hủy cài đặt nhắc nhở!",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    try:
        day = int(text)
        if day < 1 or day > 28:
            await update.message.reply_text(
                "❌ Vui lòng chọn ngày từ 1-28!"
            )
            return SET_REMINDER_DAY
        
        context.user_data['reminder_day'] = day
        
        keyboard = [
            ['07:00', '08:00', '09:00'],
            ['10:00', '14:00', '18:00'],
            ['20:00', '❌ Hủy']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        
        await update.message.reply_text(
            f"✅ Đã chọn ngày <b>{day}</b> hàng tháng\n\n"
            "Giờ bạn muốn được nhắc? (hoặc nhập tùy chỉnh theo format HH:MM)",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        return SET_REMINDER_TIME
        
    except ValueError:
        await update.message.reply_text("❌ Vui lòng nhập số hợp lệ!")
        return SET_REMINDER_DAY


async def reminder_time_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nhận giờ nhắc nhở và lưu"""
    text = update.message.text
    
    if text == '❌ Hủy':
        await update.message.reply_text(
            "Đã hủy cài đặt nhắc nhở!",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    try:
        # Validate time format
        hour, minute = text.split(':')
        hour, minute = int(hour), int(minute)
        
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError
        
        # Lưu vào database
        chat_id = str(update.effective_chat.id)
        data = load_data(chat_id)

        # Lấy danh sách phòng đã có
        rooms = list(data['rooms'].keys()) if data['rooms'] else []

        data['reminders'][chat_id] = {
            'day': context.user_data['reminder_day'],
            'time': text,
            'rooms': rooms,
            'enabled': True
        }

        save_data(chat_id, data)
        
        # Schedule job
        await schedule_reminder(context.application, chat_id, data['reminders'][chat_id])
        
        room_list = "\n".join([f"   • {r}" for r in rooms]) if rooms else "   (Chưa có phòng nào)"
        
        await update.message.reply_text(
            f"✅ <b>ĐÃ CÀI ĐẶT NHẮC NHỞ THÀNH CÔNG!</b>\n\n"
            f"📅 Ngày: Mỗi tháng vào ngày <b>{context.user_data['reminder_day']}</b>\n"
            f"⏰ Giờ: <b>{text}</b>\n"
            f"🏠 Phòng sẽ nhắc:\n{room_list}\n\n"
            f"💡 Bot sẽ tự động gửi thông báo nhắc bạn tính tiền!\n"
            f"Dùng /xemnhacnho để kiểm tra, /tatnhacnho để tắt",
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove()
        )
        
        context.user_data.clear()
        return ConversationHandler.END
        
    except (ValueError, AttributeError):
        await update.message.reply_text(
            "❌ Format giờ không đúng! Vui lòng nhập theo định dạng HH:MM\n"
            "Ví dụ: 09:00, 14:30, 20:15"
        )
        return SET_REMINDER_TIME


async def view_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xem lịch nhắc nhở hiện tại"""
    chat_id = str(update.effective_chat.id)
    data = load_data(chat_id)
    
    if chat_id not in data.get('reminders', {}):
        await update.message.reply_text(
            "📭 Bạn chưa cài đặt nhắc nhở!\n\n"
            "Dùng /nhacnho để cài đặt nhé!"
        )
        return
    
    reminder = data['reminders'][chat_id]
    status = "🟢 Đang bật" if reminder.get('enabled', True) else "🔴 Đã tắt"
    
    room_list = "\n".join([f"   • {r}" for r in reminder.get('rooms', [])]) if reminder.get('rooms') else "   (Chưa có phòng nào)"
    
    await update.message.reply_text(
        f"⏰ <b>LỊCH NHẮC NHỞ CỦA BẠN</b>\n\n"
        f"📅 Ngày: Mỗi tháng vào ngày <b>{reminder['day']}</b>\n"
        f"⏰ Giờ: <b>{reminder['time']}</b>\n"
        f"📊 Trạng thái: {status}\n"
        f"🏠 Phòng sẽ nhắc:\n{room_list}\n\n"
        f"Dùng /nhacnho để thay đổi, /tatnhacnho để tắt",
        parse_mode='HTML'
    )


async def disable_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tắt nhắc nhở"""
    chat_id = str(update.effective_chat.id)
    data = load_data(chat_id)

    if chat_id not in data.get('reminders', {}):
        await update.message.reply_text("Bạn chưa có nhắc nhở nào để tắt!")
        return

    data['reminders'][chat_id]['enabled'] = False
    save_data(chat_id, data)
    
    # Remove scheduled job
    job_name = f"reminder_{chat_id}"
    current_jobs = context.application.job_queue.get_jobs_by_name(job_name)
    for job in current_jobs:
        job.schedule_removal()
    
    await update.message.reply_text(
        "🔴 Đã tắt nhắc nhở!\n\n"
        "Dùng /nhacnho để bật lại"
    )


async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Gửi thông báo nhắc nhở"""
    job = context.job
    chat_id = job.data['chat_id']
    rooms = job.data['rooms']
    
    room_list = "\n".join([f"   • {r}" for r in rooms]) if rooms else ""
    
    message = f"""
🔔 <b>NHẮC NHỞ TÍNH TIỀN PHÒNG</b>

Đã đến thời gian tính tiền phòng tháng này rồi! 📅

🏠 <b>Phòng cần tính:</b>
{room_list}

Dùng lệnh /tinh để bắt đầu nhé! 💰

━━━━━━━━━━━━━━━━
<i>Tin nhắn tự động từ Bot Quản lý Phòng Trọ</i>
"""
    
    try:
        await context.bot.send_message(
            chat_id=int(chat_id),
            text=message,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Lỗi gửi reminder cho {chat_id}: {e}")


async def schedule_reminder(application, chat_id, reminder_data):
    """Lên lịch nhắc nhở"""
    if not reminder_data.get('enabled', True):
        return
    
    # Parse time
    hour, minute = map(int, reminder_data['time'].split(':'))
    reminder_time = time(hour=hour, minute=minute, second=0)
    
    # Tạo job name
    job_name = f"reminder_{chat_id}"
    
    # Xóa job cũ nếu có
    current_jobs = application.job_queue.get_jobs_by_name(job_name)
    for job in current_jobs:
        job.schedule_removal()
    
    # Tạo job mới - chạy hàng ngày, check ngày trong callback
    application.job_queue.run_daily(
        callback=send_reminder,
        time=reminder_time,
        data={
            'chat_id': chat_id,
            'rooms': reminder_data.get('rooms', []),
            'target_day': reminder_data['day']
        },
        name=job_name
    )
    
    print(f"✅ Đã lên lịch reminder cho chat {chat_id} vào {reminder_data['day']} hàng tháng lúc {reminder_data['time']}")


async def post_init(application):
    data_map = load_all_reminders()
    for chat_id, reminder_data in data_map.items():
        if reminder_data.get('enabled', True):
            await schedule_reminder(application, chat_id, reminder_data)


# === CÁC HÀM TÍNH TIỀN (giữ nguyên như trước) ===

async def calculate_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bắt đầu quá trình tính tiền"""
    await update.message.reply_text(
        "📝 <b>Bắt đầu tính tiền phòng</b>\n\n"
        "Nhập tên phòng (VD: Phòng 101, A1, etc.):",
        parse_mode='HTML'
    )
    return ROOM_NAME


async def room_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nhận tên phòng"""
    chat_id = str(update.effective_chat.id)
    context.user_data['room_name'] = update.message.text
    data = load_data(chat_id)

    room_data = data['rooms'].get(update.message.text, {})
    suggestion = ""
    
    if room_data and 'history' in room_data and room_data['history']:
        last_record = room_data['history'][-1]
        suggestion = f"\n💡 Số cũ tháng trước: {last_record['new_electric']}"
    
    await update.message.reply_text(
        f"⚡ Nhập số điện <b>CŨ</b>:{suggestion}",
        parse_mode='HTML'
    )
    return OLD_ELECTRIC


async def old_electric_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nhận số điện cũ"""
    try:
        context.user_data['old_electric'] = float(update.message.text)
        await update.message.reply_text("⚡ Nhập số điện <b>MỚI</b>:", parse_mode='HTML')
        return NEW_ELECTRIC
    except ValueError:
        await update.message.reply_text("❌ Vui lòng nhập số hợp lệ!")
        return OLD_ELECTRIC


async def new_electric_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nhận số điện mới"""
    try:
        new_val = float(update.message.text)
        if new_val < context.user_data['old_electric']:
            await update.message.reply_text("❌ Số mới phải lớn hơn số cũ!")
            return NEW_ELECTRIC
        
        context.user_data['new_electric'] = new_val

        chat_id = str(update.effective_chat.id)
        data = load_data(chat_id)
        room_data = data['rooms'].get(context.user_data['room_name'], {})
        suggestion = ""
        
        if room_data and 'history' in room_data and room_data['history']:
            last_record = room_data['history'][-1]
            suggestion = f"\n💡 Số cũ tháng trước: {last_record['new_water']}"
        
        await update.message.reply_text(
            f"💧 Nhập số nước <b>CŨ</b>:{suggestion}",
            parse_mode='HTML'
        )
        return OLD_WATER
    except ValueError:
        await update.message.reply_text("❌ Vui lòng nhập số hợp lệ!")
        return NEW_ELECTRIC


async def old_water_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nhận số nước cũ"""
    try:
        context.user_data['old_water'] = float(update.message.text)
        await update.message.reply_text("💧 Nhập số nước <b>MỚI</b>:", parse_mode='HTML')
        return NEW_WATER
    except ValueError:
        await update.message.reply_text("❌ Vui lòng nhập số hợp lệ!")
        return OLD_WATER


async def new_water_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nhận số nước mới và tính toán"""
    try:
        new_val = float(update.message.text)
        if new_val < context.user_data['old_water']:
            await update.message.reply_text("❌ Số mới phải lớn hơn số cũ!")
            return NEW_WATER
        
        context.user_data['new_water'] = new_val

        chat_id = str(update.effective_chat.id)
        data = load_data(chat_id)
        prices = data['prices']
        
        electric_used = context.user_data['new_electric'] - context.user_data['old_electric']
        water_used = context.user_data['new_water'] - context.user_data['old_water']
        
        electric_cost = electric_used * prices['electric_price']
        water_cost = water_used * prices['water_price']
        
        total = (prices['room_price'] + electric_cost + water_cost + 
                prices['internet'] + prices['parking'])
        
        # Custom fees
        custom_fees = data.get('custom_fees', {})
        settings = data.get('settings', {})
        invoice_format = settings.get('invoice_format', 'full')

        custom_total = 0
        custom_details = {}
        for fee_name, fee_data in custom_fees.items():
            fee_cost = fee_data['price'] * fee_data['multiplier']
            custom_total += fee_cost
            custom_details[fee_name] = fee_cost

        total = (prices['room_price'] + electric_cost + water_cost +
                prices['internet'] + prices['parking'] + custom_total)

        # Tạo hóa đơn theo format
        if invoice_format == 'simple':
            invoice = f"""
🧾 <b>HÓA ĐƠN</b>

🏠 {context.user_data['room_name']} - {datetime.now().strftime('%m/%Y')}

💰 Phòng: {prices['room_price']:,}đ
⚡ Điện: {electric_cost:,.0f}đ ({electric_used:.1f} kWh)
💧 Nước: {water_cost:,.0f}đ ({water_used:.1f} m³)
📡 Net: {prices['internet']:,}đ
🏍️ Xe: {prices['parking']:,}đ"""

            if custom_details:
                for fee_name, fee_cost in custom_details.items():
                    invoice += f"\n💵 {fee_name}: {fee_cost:,.0f}đ"

            invoice += f"""

💵 <b>TỔNG: {total:,.0f} VNĐ</b>

Xác nhận? (Có/Không)
"""

        elif invoice_format == 'detailed':
            progress_electric = "▓" * min(int(electric_used / 10), 10) + "░" * max(10 - int(electric_used / 10), 0)
            progress_water = "▓" * min(int(water_used), 10) + "░" * max(10 - int(water_used), 0)

            invoice = f"""
🧾 <b>HÓA ĐƠN CHI TIẾT</b>
{'═' * 30}

🏠 <b>Phòng:</b> {context.user_data['room_name']}
📅 <b>Tháng:</b> {datetime.now().strftime('%m/%Y')}
🕐 <b>Ngày tạo:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}

{'─' * 30}

💰 <b>CHI TIẾT THANH TOÁN:</b>

🏠 <b>Tiền phòng:</b>
   💵 {prices['room_price']:,} VNĐ

⚡ <b>Tiền điện:</b>
   📊 Chỉ số: {context.user_data['old_electric']:.1f} → {context.user_data['new_electric']:.1f}
   📈 Tiêu thụ: {electric_used:.1f} kWh
   {progress_electric}
   💲 Đơn giá: {prices['electric_price']:,}đ/kWh
   💵 <b>Thành tiền: {electric_cost:,.0f} VNĐ</b>

💧 <b>Tiền nước:</b>
   📊 Chỉ số: {context.user_data['old_water']:.1f} → {context.user_data['new_water']:.1f}
   📈 Tiêu thụ: {water_used:.1f} m³
   {progress_water}
   💲 Đơn giá: {prices['water_price']:,}đ/m³
   💵 <b>Thành tiền: {water_cost:,.0f} VNĐ</b>

📡 <b>Internet:</b> {prices['internet']:,} VNĐ
🏍️ <b>Gửi xe:</b> {prices['parking']:,} VNĐ"""

            if custom_details:
                invoice += "\n\n💵 <b>PHÍ KHÁC:</b>"
                for fee_name, fee_cost in custom_details.items():
                    invoice += f"\n   • {fee_name}: {fee_cost:,.0f}đ"

            invoice += f"""

{'═' * 30}
💵 <b>TỔNG CỘNG: {total:,.0f} VNĐ</b>
{'═' * 30}

Xác nhận lưu? (Có/Không)
"""

        else:  # full (default)
            invoice = f"""
🧾 <b>HÓA ĐƠN TIỀN PHÒNG</b>
━━━━━━━━━━━━━━━━━━━━

🏠 <b>Phòng:</b> {context.user_data['room_name']}
📅 <b>Tháng:</b> {datetime.now().strftime('%m/%Y')}

━━━━━━━━━━━━━━━━━━━━

💰 <b>CHI TIẾT:</b>

🏠 Tiền phòng: {prices['room_price']:,} VNĐ

⚡ Tiền điện:
   • Cũ: {context.user_data['old_electric']:.1f} → Mới: {context.user_data['new_electric']:.1f}
   • Tiêu thụ: {electric_used:.1f} kWh × {prices['electric_price']:,}đ
   • <b>Thành tiền: {electric_cost:,.0f} VNĐ</b>

💧 Tiền nước:
   • Cũ: {context.user_data['old_water']:.1f} → Mới: {context.user_data['new_water']:.1f}
   • Tiêu thụ: {water_used:.1f} m³ × {prices['water_price']:,}đ
   • <b>Thành tiền: {water_cost:,.0f} VNĐ</b>

📡 Internet: {prices['internet']:,} VNĐ
🏍️ Gửi xe: {prices['parking']:,} VNĐ"""

            if custom_details:
                for fee_name, fee_cost in custom_details.items():
                    invoice += f"\n💵 {fee_name}: {fee_cost:,.0f} VNĐ"

            invoice += f"""

━━━━━━━━━━━━━━━━━━━━
💵 <b>TỔNG CỘNG: {total:,.0f} VNĐ</b>
━━━━━━━━━━━━━━━━━━━━

Xác nhận lưu? (Có/Không)
"""
        
        context.user_data['invoice'] = invoice
        context.user_data['total'] = total
        context.user_data['electric_used'] = electric_used
        context.user_data['water_used'] = water_used
        context.user_data['electric_cost'] = electric_cost
        context.user_data['water_cost'] = water_cost
        context.user_data['custom_fees'] = custom_details
        
        keyboard = [['Có', 'Không']]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        
        await update.message.reply_text(invoice, parse_mode='HTML', reply_markup=reply_markup)
        return CONFIRM
        
    except ValueError:
        await update.message.reply_text("❌ Vui lòng nhập số hợp lệ!")
        return NEW_WATER


async def confirm_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xác nhận và lưu dữ liệu"""
    response = update.message.text.lower()
    
    if response in ['có', 'co', 'yes', 'y']:
        chat_id = str(update.effective_chat.id)
        data = load_data(chat_id)
        room_name = context.user_data['room_name']

        if room_name not in data['rooms']:
            data['rooms'][room_name] = {'history': []}

            # Cập nhật danh sách phòng trong reminder
            if chat_id in data.get('reminders', {}):
                if room_name not in data['reminders'][chat_id].get('rooms', []):
                    data['reminders'][chat_id].setdefault('rooms', []).append(room_name)
        
        record = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'month': datetime.now().strftime('%m/%Y'),
            'old_electric': context.user_data['old_electric'],
            'new_electric': context.user_data['new_electric'],
            'electric_used': context.user_data['electric_used'],
            'electric_cost': context.user_data['electric_cost'],
            'old_water': context.user_data['old_water'],
            'new_water': context.user_data['new_water'],
            'water_used': context.user_data['water_used'],
            'water_cost': context.user_data['water_cost'],
            'total': context.user_data['total'],
            'prices_snapshot': data['prices'].copy()
        }
        
        data['rooms'][room_name]['history'].append(record)
        save_data(chat_id, data)

        await update.message.reply_text(
            "✅ <b>Đã lưu thành công!</b>\n\n"
            "• /lichsu - Xem lịch sử\n"
            "• /tinh - Tính phòng khác\n"
            "• /nhacnho - Cài nhắc nhở tự động",
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text(
            "❌ Đã hủy!",
            reply_markup=ReplyKeyboardRemove()
        )
    
    context.user_data.clear()
    return ConversationHandler.END


async def view_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xem lịch sử thanh toán"""
    chat_id = str(update.effective_chat.id)
    data = load_data(chat_id)

    if not data['rooms']:
        await update.message.reply_text("📭 Chưa có dữ liệu!")
        return

    settings = data.get('settings', {})
    stats_format = settings.get('stats_format', 'simple')

    history_text = "📊 <b>LỊCH SỬ THANH TOÁN</b>\n\n"

    for room_name, room_data in data['rooms'].items():
        if 'history' in room_data and room_data['history']:
            history_text += f"🏠 <b>{room_name}</b>\n━━━━━━━━━\n"

            for record in room_data['history'][-3:]:
                if stats_format == 'simple':
                    history_text += f"""📅 {record['month']} → 💵 {record['total']:,.0f}đ
"""
                elif stats_format == 'detailed':
                    history_text += f"""📅 {record['month']} ({record.get('date', 'N/A')})
   🏠 Phòng: {record.get('prices_snapshot', {}).get('room_price', 0):,.0f}đ
   ⚡ Điện: {record['old_electric']:.1f} → {record['new_electric']:.1f} ({record['electric_used']:.1f} kWh × {record.get('prices_snapshot', {}).get('electric_price', 0):,}đ) = {record['electric_cost']:,.0f}đ
   💧 Nước: {record['old_water']:.1f} → {record['new_water']:.1f} ({record['water_used']:.1f} m³ × {record.get('prices_snapshot', {}).get('water_price', 0):,}đ) = {record['water_cost']:,.0f}đ
   📡 Internet: {record.get('prices_snapshot', {}).get('internet', 0):,.0f}đ
   🏍️ Xe: {record.get('prices_snapshot', {}).get('parking', 0):,.0f}đ
   💵 <b>Tổng: {record['total']:,.0f}đ</b>

"""
                else:  # full
                    history_text += f"""📅 {record['month']}
   ⚡ Điện: {record['electric_used']:.1f} kWh → {record['electric_cost']:,.0f}đ
   💧 Nước: {record['water_used']:.1f} m³ → {record['water_cost']:,.0f}đ
   💵 Tổng: {record['total']:,.0f}đ

"""

    await update.message.reply_text(history_text, parse_mode='HTML')


async def update_price_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cập nhật giá"""
    keyboard = [
        ['🏠 Tiền phòng', '⚡ Giá điện'],
        ['💧 Giá nước', '📡 Internet'],
        ['🏍️ Gửi xe', '❌ Hủy']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    
    await update.message.reply_text(
        "Chọn loại giá cần cập nhật:",
        reply_markup=reply_markup
    )
    return UPDATE_PRICE_TYPE


async def update_price_type_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nhận loại giá"""
    choice = update.message.text
    
    price_mapping = {
        '🏠 Tiền phòng': 'room_price',
        '⚡ Giá điện': 'electric_price',
        '💧 Giá nước': 'water_price',
        '📡 Internet': 'internet',
        '🏍️ Gửi xe': 'parking',
    }
    
    if choice == '❌ Hủy':
        await update.message.reply_text("Đã hủy!", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    
    if choice not in price_mapping:
        await update.message.reply_text("Lựa chọn không hợp lệ!")
        return UPDATE_PRICE_TYPE
    
    context.user_data['price_type'] = price_mapping[choice]
    context.user_data['price_label'] = choice
    
    await update.message.reply_text(
        f"Nhập giá mới cho {choice} (VNĐ):",
        reply_markup=ReplyKeyboardRemove()
    )
    return UPDATE_PRICE_VALUE


async def update_price_value_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cập nhật giá"""
    try:
        new_price = int(update.message.text)
        
        if new_price < 0:
            await update.message.reply_text("Giá phải >= 0!")
            return UPDATE_PRICE_VALUE
        
        chat_id = str(update.effective_chat.id)
        data = load_data(chat_id)
        old_price = data['prices'][context.user_data['price_type']]
        data['prices'][context.user_data['price_type']] = new_price
        save_data(chat_id, data)

        await update.message.reply_text(
            f"✅ Đã cập nhật {context.user_data['price_label']}\n"
            f"Cũ: {old_price:,}đ → Mới: {new_price:,}đ"
        )
        
        context.user_data.clear()
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("Nhập số hợp lệ!")
        return UPDATE_PRICE_VALUE


async def adjust_number_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bắt đầu sửa số điện/nước cũ"""
    chat_id = str(update.effective_chat.id)
    data = load_data(chat_id)

    if not data['rooms']:
        await update.message.reply_text("❌ Chưa có phòng nào trong hệ thống!")
        return ConversationHandler.END

    room_buttons = [[room] for room in data['rooms'].keys()]
    room_buttons.append(['❌ Hủy'])
    reply_markup = ReplyKeyboardMarkup(room_buttons, one_time_keyboard=True)

    await update.message.reply_text(
        "🔧 <b>SỬA SỐ ĐIỆN/NƯỚC CŨ</b>\n\n"
        "Chọn phòng cần sửa:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )
    return ADJUST_ROOM


async def adjust_room_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nhận tên phòng cần sửa"""
    room = update.message.text

    if room == '❌ Hủy':
        await update.message.reply_text("Đã hủy!", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    chat_id = str(update.effective_chat.id)
    data = load_data(chat_id)
    if room not in data['rooms'] or not data['rooms'][room].get('history'):
        await update.message.reply_text("❌ Phòng không tồn tại hoặc chưa có lịch sử!", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    context.user_data['adjust_room'] = room
    last = data['rooms'][room]['history'][-1]

    keyboard = [
        ['⚡ Điện cũ', '⚡ Điện mới'],
        ['💧 Nước cũ', '💧 Nước mới'],
        ['❌ Hủy']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        f"📊 <b>Bản ghi cuối của {room}:</b>\n"
        f"⚡ Điện: {last['old_electric']} → {last['new_electric']}\n"
        f"💧 Nước: {last['old_water']} → {last['new_water']}\n\n"
        f"Chọn số cần sửa:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )
    return ADJUST_TYPE


async def adjust_type_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nhận loại số cần sửa"""
    choice = update.message.text

    if choice == '❌ Hủy':
        await update.message.reply_text("Đã hủy!", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return ConversationHandler.END

    type_map = {
        '⚡ Điện cũ': 'old_electric',
        '⚡ Điện mới': 'new_electric',
        '💧 Nước cũ': 'old_water',
        '💧 Nước mới': 'new_water'
    }

    if choice not in type_map:
        await update.message.reply_text("❌ Lựa chọn không hợp lệ!")
        return ADJUST_TYPE

    context.user_data['adjust_type'] = type_map[choice]
    context.user_data['adjust_label'] = choice

    await update.message.reply_text(
        f"Nhập giá trị mới cho {choice}:",
        reply_markup=ReplyKeyboardRemove()
    )
    return ADJUST_VALUE


async def adjust_value_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nhận và cập nhật giá trị mới"""
    try:
        new_value = float(update.message.text)

        chat_id = str(update.effective_chat.id)
        data = load_data(chat_id)
        room = context.user_data['adjust_room']
        field = context.user_data['adjust_type']

        old_value = data['rooms'][room]['history'][-1][field]
        data['rooms'][room]['history'][-1][field] = new_value

        # Tính lại nếu cần
        last = data['rooms'][room]['history'][-1]
        prices = last.get('prices_snapshot', data['prices'])

        if 'electric' in field:
            last['electric_used'] = last['new_electric'] - last['old_electric']
            last['electric_cost'] = last['electric_used'] * prices['electric_price']
        elif 'water' in field:
            last['water_used'] = last['new_water'] - last['old_water']
            last['water_cost'] = last['water_used'] * prices['water_price']

        # Tính lại tổng
        last['total'] = (prices['room_price'] + last['electric_cost'] +
                        last['water_cost'] + prices['internet'] + prices['parking'])

        save_data(chat_id, data)

        await update.message.reply_text(
            f"✅ <b>Đã cập nhật!</b>\n\n"
            f"🏠 Phòng: {room}\n"
            f"📝 {context.user_data['adjust_label']}\n"
            f"Cũ: {old_value} → Mới: {new_value}\n"
            f"💵 Tổng tiền mới: {last['total']:,.0f} VNĐ",
            parse_mode='HTML'
        )

        context.user_data.clear()
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("❌ Vui lòng nhập số hợp lệ!")
        return ADJUST_VALUE


async def add_fee_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Thêm phí tùy chỉnh mới"""
    await update.message.reply_text(
        "💰 <b>THÊM PHÍ TÙY CHỈNH</b>\n\n"
        "Nhập tên phí (VD: Phí vệ sinh, Thang máy, etc.):",
        parse_mode='HTML'
    )
    return ADD_FEE_NAME


async def add_fee_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nhận tên phí"""
    context.user_data['fee_name'] = update.message.text
    await update.message.reply_text(
        f"💵 Nhập mệnh giá cho <b>{update.message.text}</b> (VNĐ):",
        parse_mode='HTML'
    )
    return ADD_FEE_PRICE


async def add_fee_price_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nhận giá phí"""
    try:
        context.user_data['fee_price'] = int(update.message.text)
        await update.message.reply_text(
            "🔢 Nhập hệ số (multiplier):\n"
            "• 0 = Tính theo người (nhập khi tính tiền)\n"
            "• 1 = Cố định (mặc định)\n"
            "• Số khác = Nhân với hệ số đó"
        )
        return ADD_FEE_MULTIPLIER
    except ValueError:
        await update.message.reply_text("❌ Vui lòng nhập số hợp lệ!")
        return ADD_FEE_PRICE


async def add_fee_multiplier_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nhận hệ số và lưu phí"""
    try:
        multiplier = float(update.message.text)

        chat_id = str(update.effective_chat.id)
        data = load_data(chat_id)
        fee_name = context.user_data['fee_name']

        data['custom_fees'][fee_name] = {
            'price': context.user_data['fee_price'],
            'multiplier': multiplier
        }

        save_data(chat_id, data)

        await update.message.reply_text(
            f"✅ <b>Đã thêm phí mới!</b>\n\n"
            f"📝 Tên: {fee_name}\n"
            f"💵 Giá: {context.user_data['fee_price']:,} VNĐ\n"
            f"🔢 Hệ số: {multiplier}",
            parse_mode='HTML'
        )

        context.user_data.clear()
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("❌ Vui lòng nhập số hợp lệ!")
        return ADD_FEE_MULTIPLIER


async def settings_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cài đặt hiển thị"""
    chat_id = str(update.effective_chat.id)
    data = load_data(chat_id)
    settings = data.get('settings', {})

    keyboard = [
        ['📄 Kiểu hóa đơn', '📊 Kiểu thống kê'],
        ['✅ Xong']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        f"⚙️ <b>CÀI ĐẶT HIỂN THỊ</b>\n\n"
        f"📄 Hóa đơn: <b>{settings.get('invoice_format', 'full')}</b>\n"
        f"📊 Thống kê: <b>{settings.get('stats_format', 'simple')}</b>\n\n"
        f"Chọn loại cần thay đổi:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )
    return SETTINGS_TYPE


async def settings_handler_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý tất cả các bước trong settings"""
    choice = update.message.text

    # Bước 1: Chọn loại settings hoặc thoát
    if choice == '✅ Xong':
        await update.message.reply_text("✅ Hoàn tất!", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return ConversationHandler.END

    if choice == '❌ Hủy':
        await update.message.reply_text("Đã hủy!", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return ConversationHandler.END

    # Bước 2: Nếu chọn invoice/stats, hiển thị options
    if choice == '📄 Kiểu hóa đơn':
        context.user_data['setting_key'] = 'invoice_format'
        msg = "Chọn kiểu hiển thị hóa đơn:"
        keyboard = [
            ['simple', 'full', 'detailed'],
            ['❌ Hủy']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text(
            f"{msg}\n\n"
            f"• <b>simple</b>: Đơn giản, gọn nhẹ\n"
            f"• <b>full</b>: Đầy đủ thông tin\n"
            f"• <b>detailed</b>: Chi tiết, có biểu đồ",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        return SETTINGS_TYPE

    elif choice == '📊 Kiểu thống kê':
        context.user_data['setting_key'] = 'stats_format'
        msg = "Chọn kiểu hiển thị thống kê:"
        keyboard = [
            ['simple', 'full', 'detailed'],
            ['❌ Hủy']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text(
            f"{msg}\n\n"
            f"• <b>simple</b>: Đơn giản, gọn nhẹ\n"
            f"• <b>full</b>: Đầy đủ thông tin\n"
            f"• <b>detailed</b>: Chi tiết, có biểu đồ",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        return SETTINGS_TYPE

    # Bước 3: Nếu chọn giá trị (simple/full/detailed), lưu và quay lại
    elif choice in ['simple', 'full', 'detailed']:
        chat_id = str(update.effective_chat.id)
        data = load_data(chat_id)
        key = context.user_data.get('setting_key')

        if key:
            data['settings'][key] = choice
            save_data(chat_id, data)
            await update.message.reply_text(f"✅ Đã cập nhật {key} = {choice}")

        context.user_data.clear()
        await settings_start(update, context)
        return SETTINGS_TYPE

    # Nếu không match gì, quay lại menu
    else:
        await settings_start(update, context)
        return SETTINGS_TYPE


async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xuất dữ liệu"""
    chat_id = str(update.effective_chat.id)
    data = load_data(chat_id)
    content = json.dumps(data, ensure_ascii=False, indent=2)
    f = io.BytesIO(content.encode('utf-8'))
    await update.message.reply_document(
        document=f,
        filename=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        caption="📦 Backup dữ liệu"
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hủy"""
    await update.message.reply_text("❌ Đã hủy!", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END


def run_health_server():
    port = int(os.getenv('PORT', 8080))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')

        def log_message(self, format, *args):
            pass

    HTTPServer(('0.0.0.0', port), Handler).serve_forever()


def main():
    """Main function"""
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        print("❌ Chưa set TELEGRAM_BOT_TOKEN!")
        print("Tạo file .env với nội dung:")
        print("TELEGRAM_BOT_TOKEN=your_token_here")
        return

    asyncio.set_event_loop(asyncio.new_event_loop())
    threading.Thread(target=run_health_server, daemon=True).start()
    init_db()
    application = Application.builder().token(TOKEN).post_init(post_init).build()
    
    # Conversation handlers
    calc_handler = ConversationHandler(
        entry_points=[CommandHandler('tinh', calculate_start)],
        states={
            ROOM_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, room_name_received)],
            OLD_ELECTRIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, old_electric_received)],
            NEW_ELECTRIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_electric_received)],
            OLD_WATER: [MessageHandler(filters.TEXT & ~filters.COMMAND, old_water_received)],
            NEW_WATER: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_water_received)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_save)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    reminder_handler = ConversationHandler(
        entry_points=[CommandHandler('nhacnho', set_reminder_start)],
        states={
            SET_REMINDER_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, reminder_day_received)],
            SET_REMINDER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reminder_time_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    price_handler = ConversationHandler(
        entry_points=[CommandHandler('capnhatgia', update_price_start)],
        states={
            UPDATE_PRICE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_price_type_received)],
            UPDATE_PRICE_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_price_value_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    adjust_handler = ConversationHandler(
        entry_points=[CommandHandler('suaso', adjust_number_start)],
        states={
            ADJUST_ROOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, adjust_room_received)],
            ADJUST_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, adjust_type_received)],
            ADJUST_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, adjust_value_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    fee_handler = ConversationHandler(
        entry_points=[CommandHandler('themphi', add_fee_start)],
        states={
            ADD_FEE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_fee_name_received)],
            ADD_FEE_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_fee_price_received)],
            ADD_FEE_MULTIPLIER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_fee_multiplier_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    settings_handler = ConversationHandler(
        entry_points=[CommandHandler('caidat', settings_start)],
        states={
            SETTINGS_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_handler_func)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("gia", show_prices))
    application.add_handler(CommandHandler("lichsu", view_history))
    application.add_handler(CommandHandler("xemnhacnho", view_reminder))
    application.add_handler(CommandHandler("tatnhacnho", disable_reminder))
    application.add_handler(CommandHandler("export", export_data))
    application.add_handler(calc_handler)
    application.add_handler(reminder_handler)
    application.add_handler(price_handler)
    application.add_handler(adjust_handler)
    application.add_handler(fee_handler)
    application.add_handler(settings_handler)
    
    print("🤖 Bot đang chạy với tính năng nhắc nhở tự động...")
    print(f"📊 Giá: {DEFAULT_PRICES}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
