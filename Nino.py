import os
import requests
import time
import json
import sqlite3
from datetime import datetime
import random
import string

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "8721247040:AAHjEQdoPUQwyUjfSl7-zOZRE0k4OUoUHbo"

# СПИСОК АДМИНОВ
ADMIN_IDS = [
    7838556865,
    6498758813,
    7092403802,
]


# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect('nino_bot.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            fullname TEXT,
            age INTEGER,
            username TEXT,
            registered_at TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meets (
            meet_id INTEGER PRIMARY KEY AUTOINCREMENT,
            meet_name TEXT,
            meet_date TEXT,
            meet_time TEXT,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT
        )
    ''')

    cursor.execute("PRAGMA table_info(meets)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'created_by' not in columns:
        cursor.execute('ALTER TABLE meets ADD COLUMN created_by INTEGER DEFAULT 0')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            meet_id INTEGER,
            code TEXT,
            status TEXT DEFAULT 'waiting',
            registered_at TEXT,
            checked_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (meet_id) REFERENCES meets(meet_id)
        )
    ''')

    conn.commit()
    conn.close()


init_db()


# ========== ФУНКЦИИ БАЗЫ ДАННЫХ ==========
def add_user(user_id, fullname, age, username):
    conn = sqlite3.connect('nino_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, fullname, age, username, registered_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, fullname, age, username, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()


def get_user(user_id):
    conn = sqlite3.connect('nino_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def get_all_users():
    conn = sqlite3.connect('nino_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, fullname, username FROM users')
    users = cursor.fetchall()
    conn.close()
    return users


def add_meet(meet_name, meet_date, meet_time, description, admin_id):
    conn = sqlite3.connect('nino_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO meets (meet_name, meet_date, meet_time, description, is_active, created_at, created_by)
        VALUES (?, ?, ?, ?, 1, ?, ?)
    ''', (meet_name, meet_date, meet_time, description, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), admin_id))
    meet_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return meet_id


def get_active_meet():
    conn = sqlite3.connect('nino_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM meets WHERE is_active = 1 ORDER BY meet_id DESC LIMIT 1')
    meet = cursor.fetchone()
    conn.close()
    return meet


def close_active_meet():
    conn = sqlite3.connect('nino_bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE meets SET is_active = 0 WHERE is_active = 1')
    conn.commit()
    conn.close()


def register_for_meet(user_id, meet_id, code):
    conn = sqlite3.connect('nino_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO registrations (user_id, meet_id, code, status, registered_at)
        VALUES (?, ?, ?, 'waiting', ?)
    ''', (user_id, meet_id, code, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()


def get_registration(user_id, meet_id):
    conn = sqlite3.connect('nino_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM registrations WHERE user_id = ? AND meet_id = ?', (user_id, meet_id))
    reg = cursor.fetchone()
    conn.close()
    return reg


def get_all_registrations(meet_id):
    conn = sqlite3.connect('nino_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.*, u.fullname, u.username 
        FROM registrations r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.meet_id = ?
        ORDER BY r.registered_at
    ''', (meet_id,))
    regs = cursor.fetchall()
    conn.close()
    return regs


def update_registration_status(user_id, meet_id, status):
    conn = sqlite3.connect('nino_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE registrations 
        SET status = ?, checked_at = ?
        WHERE user_id = ? AND meet_id = ?
    ''', (status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id, meet_id))
    conn.commit()
    conn.close()


def get_registration_by_code(meet_id, code):
    conn = sqlite3.connect('nino_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.*, u.fullname, u.username 
        FROM registrations r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.meet_id = ? AND r.code = ? AND r.status = 'waiting'
    ''', (meet_id, code))
    reg = cursor.fetchone()
    conn.close()
    return reg


def generate_code():
    return ''.join(random.choices(string.digits, k=6))


# ========== ФУНКЦИИ TELEGRAM ==========
def send_message(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if keyboard:
        payload["reply_markup"] = json.dumps(keyboard)

    try:
        response = requests.post(url, data=payload, proxies=proxies)
        return response.json()
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return None


def send_message_simple(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload, proxies=proxies)
    except Exception as e:
        print(f"Ошибка отправки: {e}")


def send_photo_by_url(chat_id, photo_url, caption=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "parse_mode": "HTML"
    }
    if caption:
        payload["caption"] = caption
    try:
        response = requests.post(url, data=payload, proxies=proxies)
        if response.status_code == 200:
            return True
        else:
            print(f"Ошибка отправки фото: {response.text}")
            return False
    except Exception as e:
        print(f"Ошибка отправки фото: {e}")
        return False


def answer_callback(callback_id, text=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    payload = {"callback_query_id": callback_id}
    if text:
        payload["text"] = text
    try:
        requests.post(url, data=payload, proxies=proxies)
    except Exception as e:
        print(f"Ошибка callback: {e}")


def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 30, "allowed_updates": ["message", "callback_query"]}
    if offset:
        params["offset"] = offset

    try:
        # Создаём сессию
        session = requests.Session()
        session.trust_env = False  # Не использовать системные прокси
        response = session.get(url, params=params, proxies=proxies, timeout=30)
        result = response.json()
        if result.get("ok"):
            return result.get("result", [])
        else:
            print(f"Ошибка API: {result}")
            return []
    except Exception as e:
        print(f"Ошибка получения обновлений: {e}")
        return []


def notify_users_about_new_meet(meet_name, meet_date, meet_time, description):
    users = get_all_users()

    if not users:
        print("Нет пользователей для уведомления")
        return

    notification_text = f"""
🎉 <b>НОВАЯ СХОДКА В NINO!</b>

━━━━━━━━━━━━━━━━━━━━━
📌 <b>{meet_name}</b>
📅 {meet_date} | ⏰ {meet_time}
📝 {description}
━━━━━━━━━━━━━━━━━━━━━

<b>Хочешь пойти?</b>
Нажми «Записаться на сходку» в главном меню бота и получи свой уникальный код!

Ждём тебя! 🔥
"""

    success_count = 0
    fail_count = 0

    for user in users:
        user_id = user[0]
        try:
            send_message_simple(user_id, notification_text)
            success_count += 1
        except Exception as e:
            fail_count += 1
            print(f"Не удалось уведомить пользователя {user_id}: {e}")

        time.sleep(0.05)

    print(f"Уведомления о новой сходке отправлены: ✅ {success_count}, ❌ {fail_count}")


# ========== КЛАВИАТУРЫ ==========
def get_main_keyboard(user_id=None):
    buttons = [[{"text": "🎫 Записаться на сходку", "callback_data": "register_for_meet"}]]

    if user_id:
        active_meet = get_active_meet()
        if active_meet:
            reg = get_registration(user_id, active_meet[0])
            if reg and reg[4] == 'waiting':
                buttons.append([{"text": "🎟️ Мой код на сходку", "callback_data": "show_my_code"}])

    buttons.append([{"text": "ℹ️ О нас", "callback_data": "about"}, {"text": "❓ Помощь", "callback_data": "help"}])

    return {"inline_keyboard": buttons}


def get_admin_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📅 Создать сходку", "callback_data": "admin_create_meet"}],
            [{"text": "🔒 Закрыть регистрацию", "callback_data": "admin_close_meet"}],
            [{"text": "📋 Список участников", "callback_data": "admin_get_list"}],
            [{"text": "🎟️ Проверить коды", "callback_data": "admin_check_codes"}],
            [{"text": "📊 Статистика сходки", "callback_data": "admin_meet_info"}],
            [{"text": "👥 Все пользователи", "callback_data": "admin_all_users"}],
            [{"text": "📢 Сделать рассылку", "callback_data": "admin_mailing"}],
            [{"text": "🎫 Записаться на сходку", "callback_data": "register_for_meet"}],
            [{"text": "👤 Моя регистрация", "callback_data": "my_registration"}]
        ]
    }


def get_confirm_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "✅ Да, приду", "callback_data": "confirm_yes"}],
            [{"text": "❌ Нет, не приду", "callback_data": "confirm_no"}]
        ]
    }


def get_mailing_type_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📝 Только текст", "callback_data": "mailing_text"}],
            [{"text": "🖼️ Текст + ссылка на фото", "callback_data": "mailing_photo"}],
            [{"text": "◀️ Назад", "callback_data": "admin_back"}]
        ]
    }


def is_admin(user_id):
    return user_id in ADMIN_IDS


def send_mailing_to_all(admin_id, text, photo_url=None):
    users = get_all_users()

    if not users:
        send_message_simple(admin_id, "❌ Нет зарегистрированных пользователей для рассылки!")
        return False, 0, 0

    success_count = 0
    fail_count = 0

    for user in users:
        user_id = user[0]
        try:
            if photo_url:
                send_photo_by_url(user_id, photo_url, text)
            else:
                send_message_simple(user_id, text)
            success_count += 1
        except Exception as e:
            fail_count += 1
            print(f"Не удалось отправить пользователю {user_id}: {e}")

        time.sleep(0.05)

    return True, success_count, fail_count


def get_active_meet_info():
    active_meet = get_active_meet()

    if active_meet:
        meet_id, meet_name, meet_date, meet_time, description, is_active, created_at, created_by = active_meet
        registrations = get_all_registrations(meet_id)
        total = len(registrations)

        return f"""
━━━━━━━━━━━━━━━━━━━━━
<b>🔥 АКТИВНАЯ СХОДКА!</b>

📌 <b>{meet_name}</b>
📅 {meet_date} | ⏰ {meet_time}
📝 {description}

👥 Уже записалось: <b>{total}</b> человек
━━━━━━━━━━━━━━━━━━━━━
"""
    else:
        return """
━━━━━━━━━━━━━━━━━━━━━
<b>😔 Активных сходок нет</b>

Загляни позже — скоро появится новая!
━━━━━━━━━━━━━━━━━━━━━
"""


def get_welcome_text(user_name):
    meet_info = get_active_meet_info()

    return f"""
<b>🌟 ДОБРО ПОЖАЛОВАТЬ В NINO, {user_name}! 🌟</b>

<b>🎯 Что такое NINO?</b>
Это эксклюзивное сообщество, где ты узнаешь о всех крутых сходках и мероприятиях первым!

<b>🔥 Что тебя ждет:</b>
• Регулярные сходки
• Закрытые мероприятия
• Новые знакомства
• Крутая атмосфера

{meet_info}

<b>📝 Зарегистрируйся и будь в курсе всех событий!</b>
"""


def get_welcome_back_text(user_name, user_id):
    meet_info = get_active_meet_info()

    active_meet = get_active_meet()
    if active_meet:
        meet_id = active_meet[0]
        existing_reg = get_registration(user_id, meet_id)
        if existing_reg and existing_reg[4] == 'waiting':
            meet_info = f"""
━━━━━━━━━━━━━━━━━━━━━
<b>🔥 АКТИВНАЯ СХОДКА!</b>

📌 <b>{active_meet[1]}</b>
📅 {active_meet[2]} | ⏰ {active_meet[3]}

✅ <b>Ты уже записан!</b>
🎫 Твой код: <code>{existing_reg[3]}</code>
━━━━━━━━━━━━━━━━━━━━━
"""
        elif existing_reg and existing_reg[4] == 'present':
            meet_info = f"""
━━━━━━━━━━━━━━━━━━━━━
<b>✅ ТЫ УЖЕ ОТМЕЧЕН НА СХОДКЕ!</b>

📌 <b>{active_meet[1]}</b>
📅 {active_meet[2]} | ⏰ {active_meet[3]}
━━━━━━━━━━━━━━━━━━━━━
"""

    return f"""
✨ <b>С возвращением, {user_name}!</b> ✨

{meet_info}

Выбери действие на кнопках ниже 👇
"""


# ========== СОСТОЯНИЯ ==========
admin_states = {}
user_states = {}


# ========== ОБРАБОТЧИКИ ==========
def process_message(message):
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    user_name = message["from"].get("first_name", "Друг")

    if "text" not in message:
        return

    text = message["text"].strip()

    print(f"📩 Получено сообщение от {user_name}: {text}")

    if text == "/start":
        welcome_text = get_welcome_text(user_name)
        user = get_user(user_id)

        if is_admin(user_id):
            if not user:
                send_message(chat_id,
                             welcome_text + "\n\n⚠️ <b>Вы администратор, но ещё не зарегистрированы!</b>\nНажмите «Записаться на сходку» для регистрации.",
                             get_main_keyboard(user_id))
            else:
                send_message(chat_id, welcome_text, None)
                send_message(chat_id, "🔧 <b>Админ-панель</b>", get_admin_keyboard())
        elif not user:
            send_message(chat_id, welcome_text, get_main_keyboard(user_id))
        else:
            welcome_back = get_welcome_back_text(user_name, user_id)
            send_message(chat_id, welcome_back, get_main_keyboard(user_id))
        return

    if text == "/admin" and is_admin(user_id):
        send_message(chat_id, "🔧 <b>Админ-панель</b>", get_admin_keyboard())
        return

    # АДМИН: СОЗДАНИЕ СХОДКИ
    if is_admin(user_id) and admin_states.get(user_id, {}).get('action'):
        action_data = admin_states[user_id]
        action = action_data['action']

        if action == 'waiting_name':
            admin_states[user_id]['meet_data'] = {'name': text}
            admin_states[user_id]['action'] = 'waiting_date'
            send_message_simple(chat_id,
                                "📅 Введите <b>дату</b> сходки\n\nПример: <code>25 декабря</code> или <code>25.12</code>")

        elif action == 'waiting_date':
            admin_states[user_id]['meet_data']['date'] = text
            admin_states[user_id]['action'] = 'waiting_time'
            send_message_simple(chat_id, "⏰ Введите <b>время</b> сходки\n\nПример: <code>19:00</code>")

        elif action == 'waiting_time':
            admin_states[user_id]['meet_data']['time'] = text
            admin_states[user_id]['action'] = 'waiting_desc'
            send_message_simple(chat_id, "📝 Введите <b>описание</b> сходки")

        elif action == 'waiting_desc':
            meet_data = admin_states[user_id]['meet_data']
            meet_id = add_meet(meet_data['name'], meet_data['date'], meet_data['time'], text, user_id)

            meet_info = f"""
✅ <b>Сходка создана!</b>

📌 <b>Название:</b> {meet_data['name']}
📅 <b>Дата:</b> {meet_data['date']}
⏰ <b>Время:</b> {meet_data['time']}
📝 <b>Описание:</b> {text}

🎉 Регистрация открыта!
"""
            send_message_simple(chat_id, meet_info)

            notify_users_about_new_meet(meet_data['name'], meet_data['date'], meet_data['time'], text)

            send_message(chat_id, "🔧 <b>Админ-панель</b>", get_admin_keyboard())
            del admin_states[user_id]
        return

    # АДМИН: ПРОВЕРКА КОДОВ
    if is_admin(user_id) and admin_states.get(user_id, {}).get('checking_codes'):
        if text == "/cancel":
            del admin_states[user_id]
            send_message(chat_id, "❌ Режим проверки отменён.\n\n🔧 <b>Админ-панель</b>", get_admin_keyboard())
        else:
            active_meet = get_active_meet()
            if not active_meet:
                send_message_simple(chat_id, "❌ Нет активной сходки!")
                return

            reg = get_registration_by_code(active_meet[0], text)
            if reg:
                reg_id, reg_user_id, meet_id, code, status, reg_time, check_time, fullname, username = reg
                update_registration_status(reg_user_id, active_meet[0], 'present')
                send_message_simple(chat_id, f"""
✅ <b>Присутствие подтверждено!</b>

👤 {fullname}
🎫 Код: <code>{code}</code>
⏰ Отмечен в: {datetime.now().strftime('%H:%M:%S')}
""")
            else:
                send_message_simple(chat_id,
                                    f"❌ <b>Неверный код!</b>\n\nКод <code>{text}</code> не найден или уже использован.")
        return

    # ========== РАССЫЛКА ==========

    # Шаг 1: Пользователь выбрал "Только текст" - ждём текст
    if is_admin(user_id) and admin_states.get(user_id, {}).get('mailing_waiting_text'):
        if text == "/cancel":
            del admin_states[user_id]
            send_message(chat_id, "❌ Создание рассылки отменено.\n\n🔧 <b>Админ-панель</b>", get_admin_keyboard())
            return

        admin_states[user_id]['mailing_text'] = text
        del admin_states[user_id]['mailing_waiting_text']
        admin_states[user_id]['mailing_step'] = 'confirm_text'

        confirm_text = f"""
📢 <b>ПРЕДПРОСМОТР РАССЫЛКИ</b>

━━━━━━━━━━━━━━━━━━━━━
{text}
━━━━━━━━━━━━━━━━━━━━━

<b>Отправить эту рассылку всем пользователям?</b>
"""
        keyboard = {
            "inline_keyboard": [
                [{"text": "✅ Да, отправить", "callback_data": "mailing_send_text"}],
                [{"text": "✏️ Ввести заново", "callback_data": "mailing_restart"}],
                [{"text": "◀️ Назад", "callback_data": "admin_back"}]
            ]
        }
        send_message(chat_id, confirm_text, keyboard)
        return

    # Шаг 2: Пользователь выбрал "Текст + ссылка на фото" - ждём текст
    if is_admin(user_id) and admin_states.get(user_id, {}).get('mailing_waiting_photo_text'):
        if text == "/cancel":
            del admin_states[user_id]
            send_message(chat_id, "❌ Создание рассылки отменено.\n\n🔧 <b>Админ-панель</b>", get_admin_keyboard())
            return

        admin_states[user_id]['mailing_text'] = text
        del admin_states[user_id]['mailing_waiting_photo_text']
        admin_states[user_id]['mailing_step'] = 'waiting_photo_url'
        send_message_simple(chat_id,
                            "🖼️ Теперь отправьте <b>прямую ссылку на фото</b>\n\nПример: <code>https://example.com/photo.jpg</code>\n\nКак получить ссылку:\n1. Отправьте фото боту @lhl_images_bot\n2. Скопируйте полученную ссылку\n3. Вставьте её сюда\n\nИли отправьте /cancel для отмены")
        return

    # Шаг 3: Ждём ссылку на фото
    if is_admin(user_id) and admin_states.get(user_id, {}).get('mailing_step') == 'waiting_photo_url':
        if text == "/cancel":
            del admin_states[user_id]
            send_message(chat_id, "❌ Создание рассылки отменено.\n\n🔧 <b>Админ-панель</b>", get_admin_keyboard())
            return

        photo_url = text
        mailing_text = admin_states[user_id].get('mailing_text', '')

        if not (photo_url.startswith('http://') or photo_url.startswith('https://')):
            send_message_simple(chat_id,
                                "❌ Это не похоже на ссылку! Отправьте ссылку, начинающуюся с http:// или https://\n\nИли отправьте /cancel для отмены")
            return

        confirm_text = f"""
📢 <b>ПРЕДПРОСМОТР РАССЫЛКИ (с фото)</b>

━━━━━━━━━━━━━━━━━━━━━
📝 <b>Текст:</b>
{mailing_text}

🖼️ <b>Ссылка на фото:</b>
{photo_url}
━━━━━━━━━━━━━━━━━━━━━

<b>Отправить эту рассылку всем пользователям?</b>
"""
        keyboard = {
            "inline_keyboard": [
                [{"text": "✅ Да, отправить", "callback_data": f"mailing_send_photo|{photo_url}"}],
                [{"text": "✏️ Ввести заново", "callback_data": "mailing_restart"}],
                [{"text": "◀️ Назад", "callback_data": "admin_back"}]
            ]
        }
        send_message(chat_id, confirm_text, keyboard)
        return

    # РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ
    if user_states.get(user_id, {}).get('waiting_name'):
        parts = text.split()
        if len(parts) < 2:
            send_message_simple(chat_id,
                                "❌ Введите <b>фамилию и имя</b> через пробел\n\nПример: <code>Иванов Иван</code>")
            return

        user_states[user_id]['fullname'] = text
        user_states[user_id]['waiting_name'] = False
        user_states[user_id]['waiting_age'] = True
        send_message_simple(chat_id, "🎂 Сколько вам <b>полных лет</b>?\n\n⚠️ Минимальный возраст — <b>14 лет</b>")
        return

    if user_states.get(user_id, {}).get('waiting_age'):
        try:
            age = int(text)
            if age < 14:
                send_message_simple(chat_id, "❌ Возраст должен быть <b>не менее 14 лет</b>!\n\nПопробуйте снова:")
                return

            fullname = user_states[user_id]['fullname']
            username = message["from"].get("username", "")

            add_user(user_id, fullname, age, username)

            meet_info = get_active_meet_info()

            welcome_msg = f"""
✅ <b>Регистрация завершена!</b>

Добро пожаловать в NINO, <b>{fullname}</b>! 🎉

{meet_info}

Теперь ты можешь записываться на сходки.
"""
            send_message_simple(chat_id, welcome_msg)

            del user_states[user_id]

            if is_admin(user_id):
                send_message(chat_id, "🔧 <b>Админ-панель</b>", get_admin_keyboard())
            else:
                send_message(chat_id, "✨ <b>Главное меню</b> ✨", get_main_keyboard(user_id))

            active_meet = get_active_meet()
            if active_meet:
                meet_id, meet_name, meet_date, meet_time, description, is_active, created_at, created_by = active_meet

                existing_reg = get_registration(user_id, meet_id)
                if not existing_reg:
                    meet_text = f"""
🎉 <b>Активная сходка!</b>

📌 <b>{meet_name}</b>
📅 {meet_date} | ⏰ {meet_time}

📝 {description}

<b>Ты придёшь?</b>
"""
                    send_message(chat_id, meet_text, get_confirm_keyboard())

        except ValueError:
            send_message_simple(chat_id, "❌ Введите <b>число</b> (ваш возраст)!")
        return


def process_callback(callback):
    callback_id = callback["id"]
    chat_id = callback["message"]["chat"]["id"]
    data = callback["data"]
    user_id = callback["from"]["id"]

    answer_callback(callback_id)

    if data == "back_to_menu":
        if is_admin(user_id):
            send_message(chat_id, "🔧 <b>Админ-панель</b>", get_admin_keyboard())
        else:
            send_message(chat_id, "✨ <b>Главное меню</b> ✨", get_main_keyboard(user_id))
        return

    if data == "admin_back":
        send_message(chat_id, "🔧 <b>Админ-панель</b>", get_admin_keyboard())
        return

    # === КРАСИВОЕ ОПИСАНИЕ NINO ===
    if data == "about":
        text = """
<b>🌟 ЧТО ТАКОЕ NINO?</b>

NINO — это не просто сообщество. Это твоя личная тусовка, где всегда происходит что-то интересное!

━━━━━━━━━━━━━━━━━━━━━
<b>🎯 ЧЕМ МЫ ЗАНИМАЕМСЯ?</b>

🔥 <b>ВСТРЕЧИ</b>
Крутые знакомства, новые друзья и море общения. Здесь ты всегда найдёшь компанию по душе!

🎲 <b>ИНТЕРАКТИВЫ</b>
Квизы, мафия, настолки, мозгобойни — скучно не будет никому!

🎉 <b>ТУСОВКИ</b>
Домашние вечеринки, квартирники, afterparty — отрываемся по полной!

🌴 <b>ОРГАНИЗАЦИЯ ОТДЫХА</b>
Выезды на природу, пикники, шашлыки, походы — отдыхаем красиво!

━━━━━━━━━━━━━━━━━━━━━
<b>💫 ПОЧЕМУ У НАС ВЕСЕЛО?</b>

• Дружелюбная атмосфера без напряга
• Всегда интересные люди
• Никакой токсичности — только позитив
• Каждый найдет занятие по душе
• Мы умеем отдыхать так, что ты захочешь вернуться!

━━━━━━━━━━━━━━━━━━━━━
<b>✨ НАШИ ПРИНЦИПЫ:</b>

• Без осуждения и предрассудков
• Уважение к каждому участнику
• Открытость новым знакомствам
• Только качественный отдых

━━━━━━━━━━━━━━━━━━━━━
<b>🔥 Присоединяйся к NINO!</b>

Стань частью движа, заведи новые знакомства и отрывайся с нами по полной!

<i>У нас всегда есть место для новых друзей!</i> 🚀
"""
        send_message_simple(chat_id, text)

    elif data == "help":
        text = """
<b>❓ Помощь</b>

<b>Как зарегистрироваться:</b>
1️⃣ Нажмите «Записаться на сходку»
2️⃣ Введите фамилию и имя
3️⃣ Укажите возраст (от 14 лет)

<b>Команды:</b>
/start - главное меню
"""
        send_message_simple(chat_id, text)

    elif data == "my_registration":
        user = get_user(user_id)
        if not user:
            send_message_simple(chat_id,
                                "❌ Вы ещё не зарегистрированы!\n\nНажмите «Записаться на сходку» для регистрации.")
        else:
            fullname, age, username, reg_time = user[1], user[2], user[3], user[4]
            text = f"""
<b>👤 Моя регистрация</b>

<b>ФИО:</b> {fullname}
<b>Возраст:</b> {age} лет
<b>Юзернейм:</b> @{username if username else 'нет'}
<b>Дата регистрации:</b> {reg_time[:10]}
"""
            send_message_simple(chat_id, text)

    elif data == "show_my_code":
        active_meet = get_active_meet()
        if not active_meet:
            send_message_simple(chat_id, "❌ Сейчас нет активных сходок!")
            return

        reg = get_registration(user_id, active_meet[0])
        if not reg:
            send_message_simple(chat_id, "❌ Вы не записаны на текущую сходку!\n\nНажмите «Записаться на сходку».")
            return

        if reg[4] == 'present':
            send_message_simple(chat_id, f"""
✅ <b>Ты уже отмечен на сходке!</b>

📌 <b>{active_meet[1]}</b>
📅 {active_meet[2]} | ⏰ {active_meet[3]}

Спасибо, что пришёл! 🎉
""")
        else:
            meet_name = active_meet[1]
            meet_date = active_meet[2]
            meet_time = active_meet[3]
            code = reg[3]

            text = f"""
🎫 <b>ТВОЙ КОД НА СХОДКУ</b>

━━━━━━━━━━━━━━━━━━━━━
📌 <b>{meet_name}</b>
📅 {meet_date} | ⏰ {meet_time}
━━━━━━━━━━━━━━━━━━━━━

<b>Код:</b> <code>{code}</code>

⚠️ <b>ВАЖНО!</b>
• Покажи этот код на входе
• Код одноразовый
• Не передавай его никому

Ждём тебя! 🔥
"""
            send_message_simple(chat_id, text)

    elif data == "register_for_meet":
        user = get_user(user_id)
        if not user:
            user_states[user_id] = {'waiting_name': True}
            send_message_simple(chat_id, """
<b>📝 Регистрация в NINO</b>

Введите ваши <b>фамилию и имя</b> через пробел:

<code>Пример: Иванов Иван</code>
""")
        else:
            active_meet = get_active_meet()
            if not active_meet:
                send_message_simple(chat_id, "❌ Сейчас нет активных сходок. Загляни позже!")
                return

            meet_id, meet_name, meet_date, meet_time, description, is_active, created_at, created_by = active_meet

            existing_reg = get_registration(user_id, meet_id)
            if existing_reg:
                if existing_reg[4] == 'waiting':
                    send_message_simple(chat_id, f"""
⚠️ <b>Вы уже записаны!</b>

📌 {meet_name}
🎫 Ваш код: <code>{existing_reg[3]}</code>

Сохраните его — он понадобится на входе!
""")
                else:
                    send_message_simple(chat_id, f"""
✅ <b>Вы уже отмечены на сходке!</b>

📌 {meet_name}
Спасибо, что пришли! 🎉
""")
                return

            meet_text = f"""
🎉 <b>Новая сходка!</b>

📌 <b>{meet_name}</b>
📅 {meet_date} | ⏰ {meet_time}

📝 {description}

<b>Ты придёшь?</b>
"""
            send_message(chat_id, meet_text, get_confirm_keyboard())

    elif data == "confirm_yes":
        active_meet = get_active_meet()
        if not active_meet:
            send_message_simple(chat_id, "❌ Сходка уже закрыта!")
            return

        meet_id, meet_name, meet_date, meet_time, description, is_active, created_at, created_by = active_meet

        existing_reg = get_registration(user_id, meet_id)
        if existing_reg:
            send_message_simple(chat_id, f"✅ Вы уже записаны!\n\nВаш код: <code>{existing_reg[3]}</code>")
            return

        code = generate_code()
        register_for_meet(user_id, meet_id, code)

        reg_text = f"""
✅ <b>Ты записан на сходку!</b>

📌 <b>{meet_name}</b>
📅 {meet_date} | ⏰ {meet_time}

━━━━━━━━━━━━━━━━━━━━━

🎫 <b>Твой одноразовый код:</b>
<code>{code}</code>

⚠️ <b>Важно!</b> Покажи этот код на входе.

Ждём тебя! 🔥
"""
        send_message_simple(chat_id, reg_text)

        if is_admin(user_id):
            send_message(chat_id, "🔧 <b>Админ-панель</b>", get_admin_keyboard())
        else:
            send_message(chat_id, "✨ <b>Главное меню</b> ✨", get_main_keyboard(user_id))

    elif data == "confirm_no":
        send_message_simple(chat_id, "😞 Жаль! В следующий раз обязательно приходи!")

    # ========== АДМИН-ПАНЕЛЬ ==========
    elif data == "admin_create_meet":
        if not is_admin(user_id):
            send_message_simple(chat_id, "⛔ У вас нет прав администратора!")
            return
        admin_states[user_id] = {'action': 'waiting_name', 'meet_data': {}}
        send_message_simple(chat_id, "📝 Введите <b>название</b> сходки:")

    elif data == "admin_close_meet":
        if not is_admin(user_id):
            return
        active_meet = get_active_meet()
        if not active_meet:
            send_message_simple(chat_id, "❌ Нет активной сходки!")
            return
        close_active_meet()
        send_message_simple(chat_id, f"🔒 <b>Регистрация закрыта!</b>")

    elif data == "admin_get_list":
        if not is_admin(user_id):
            return
        active_meet = get_active_meet()
        if not active_meet:
            send_message_simple(chat_id, "❌ Нет активной сходки!")
            return

        registrations = get_all_registrations(active_meet[0])
        if not registrations:
            send_message_simple(chat_id, "📋 Пока никто не записался.")
            return

        waiting = []
        present = []
        for reg in registrations:
            fullname = reg[7] if len(reg) > 7 else f"User{reg[1]}"
            code = reg[3]
            if reg[4] == 'waiting':
                waiting.append(f"⏳ {fullname} — код: <code>{code}</code>")
            else:
                present.append(f"✅ {fullname} — код: <code>{code}</code>")

        text = f"<b>📋 Список участников</b>\n\n"
        if waiting:
            text += "<b>⏳ Ожидают:</b>\n" + "\n".join(waiting) + "\n\n"
        if present:
            text += "<b>✅ Присутствуют:</b>\n" + "\n".join(present)
        send_message_simple(chat_id, text)

    elif data == "admin_check_codes":
        if not is_admin(user_id):
            return
        active_meet = get_active_meet()
        if not active_meet:
            send_message_simple(chat_id, "❌ Нет активной сходки! Сначала создайте сходку.")
            return

        admin_states[user_id] = {'checking_codes': True}
        send_message_simple(chat_id, f"""
🎟️ <b>Режим проверки кодов</b>

📌 Сходка: <b>{active_meet[1]}</b>

Введите код, который показал участник:

<code>/cancel</code> - выйти из режима
""")

    elif data == "admin_meet_info":
        if not is_admin(user_id):
            return
        active_meet = get_active_meet()
        if not active_meet:
            send_message_simple(chat_id, "❌ Нет активной сходки!")
            return

        meet_id, meet_name, meet_date, meet_time, description, is_active, created_at, created_by = active_meet
        registrations = get_all_registrations(meet_id)
        total = len(registrations)
        waiting = len([r for r in registrations if r[4] == 'waiting'])
        present = len([r for r in registrations if r[4] == 'present'])

        send_message_simple(chat_id, f"""
<b>📊 Статистика сходки</b>

📌 <b>{meet_name}</b>
📅 {meet_date} | ⏰ {meet_time}

<b>Статистика:</b>
• Всего записалось: {total}
• Ожидают: {waiting}
• Присутствуют: {present}

Статус: {'🟢 Активна' if is_active else '🔴 Закрыта'}
""")

    elif data == "admin_all_users":
        if not is_admin(user_id):
            return
        conn = sqlite3.connect('nino_bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT fullname, username, registered_at FROM users ORDER BY registered_at DESC')
        users = cursor.fetchall()
        conn.close()

        if not users:
            send_message_simple(chat_id, "📋 Нет зарегистрированных пользователей.")
            return

        text = "<b>👥 Все пользователи</b>\n\n"
        for u in users[:20]:
            username = f"@{u[1]}" if u[1] else "нет юзернейма"
            text += f"👤 {u[0]} ({username}) — зарегистрирован: {u[2][:10]}\n"
        send_message_simple(chat_id, text)

    # ========== РАССЫЛКА ==========
    elif data == "admin_mailing":
        if not is_admin(user_id):
            send_message_simple(chat_id, "⛔ У вас нет прав администратора!")
            return

        users_count = len(get_all_users())

        if users_count == 0:
            send_message_simple(chat_id,
                                "❌ Нет зарегистрированных пользователей для рассылки!\n\nСначала дождитесь регистрации пользователей.")
            return

        text = f"""
📢 <b>СОЗДАНИЕ РАССЫЛКИ</b>

👥 Будет отправлено <b>{users_count}</b> пользователям

Выберите тип рассылки:
"""
        send_message(chat_id, text, get_mailing_type_keyboard())

    elif data == "mailing_text":
        if not is_admin(user_id):
            return
        admin_states[user_id] = {'mailing_waiting_text': True}
        send_message_simple(chat_id,
                            "📝 Введите <b>текст</b> для рассылки:\n\nМожно использовать HTML теги\n\nИли отправьте /cancel для отмены")

    elif data == "mailing_photo":
        if not is_admin(user_id):
            return
        admin_states[user_id] = {'mailing_waiting_photo_text': True}
        send_message_simple(chat_id,
                            "📝 Введите <b>текст</b> для рассылки (будет подписью к фото):\n\nИли отправьте /cancel для отмены")

    elif data == "mailing_restart":
        if not is_admin(user_id):
            return
        if user_id in admin_states:
            del admin_states[user_id]
        send_message(chat_id, "🔄 Давай начнём заново!\n\nВыберите тип рассылки:", get_mailing_type_keyboard())

    elif data == "mailing_send_text":
        if not is_admin(user_id):
            return
        mailing_text = admin_states.get(user_id, {}).get('mailing_text', '')

        if not mailing_text:
            send_message_simple(chat_id, "❌ Текст рассылки пуст!")
            if user_id in admin_states:
                del admin_states[user_id]
            return

        send_message_simple(chat_id, "📢 Начинаю рассылку... Это может занять некоторое время.")

        success, success_count, fail_count = send_mailing_to_all(user_id, mailing_text)

        if success:
            result_text = f"""
✅ <b>Рассылка завершена!</b>

📊 <b>Статистика:</b>
• Отправлено успешно: <b>{success_count}</b>
• Не доставлено: <b>{fail_count}</b>
"""
            send_message_simple(chat_id, result_text)

        if user_id in admin_states:
            del admin_states[user_id]
        send_message(chat_id, "🔧 <b>Админ-панель</b>", get_admin_keyboard())

    elif data.startswith("mailing_send_photo"):
        if not is_admin(user_id):
            return
        photo_url = data.split("|")[1] if "|" in data else ""
        mailing_text = admin_states.get(user_id, {}).get('mailing_text', '')

        if not mailing_text:
            send_message_simple(chat_id, "❌ Текст рассылки пуст!")
            if user_id in admin_states:
                del admin_states[user_id]
            return

        send_message_simple(chat_id, "📢 Начинаю рассылку с фото... Это может занять некоторое время.")

        success, success_count, fail_count = send_mailing_to_all(user_id, mailing_text, photo_url)

        if success:
            result_text = f"""
✅ <b>Рассылка завершена!</b>

📊 <b>Статистика:</b>
• Отправлено успешно: <b>{success_count}</b>
• Не доставлено: <b>{fail_count}</b>
"""
            send_message_simple(chat_id, result_text)

        if user_id in admin_states:
            del admin_states[user_id]
        send_message(chat_id, "🔧 <b>Админ-панель</b>", get_admin_keyboard())

    elif data == "mailing_cancel":
        if not is_admin(user_id):
            return
        if user_id in admin_states:
            del admin_states[user_id]
        send_message_simple(chat_id, "❌ Создание рассылки отменено.")
        send_message(chat_id, "🔧 <b>Админ-панель</b>", get_admin_keyboard())


# ========== ОСНОВНОЙ ЦИКЛ ==========
def main():
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook", proxies=proxies)
        print("✅ Вебхук удалён")
    except:
        pass

    print("""
🚀 БОТ NINO ЗАПУЩЕН!
━━━━━━━━━━━━━━━━━━━━━
    """)

    last_update_id = 0

    while True:
        try:
            updates = get_updates(last_update_id + 1)

            for update in updates:
                last_update_id = update["update_id"]

                if "message" in update:
                    process_message(update["message"])

                elif "callback_query" in update:
                    process_callback(update["callback_query"])

            time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n👋 Бот остановлен")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(3)


if __name__ == "__main__":
    try:
        test_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        response = requests.get(test_url, proxies=proxies)
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get("ok"):
                print(f"✅ Бот: @{bot_info['result']['username']}")
                print(f"👥 Админы: {len(ADMIN_IDS)}")
            else:
                print("❌ Ошибка токена")
                exit()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        exit()

    main()
