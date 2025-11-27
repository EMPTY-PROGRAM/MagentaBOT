import telebot
import logging
import sqlite3
import os
from datetime import datetime
import time
import re

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота и данные
BOT_TOKEN = "token"
ADMIN_CHAT_ID = 324232342
ADMIN_USERNAME = "@MAGENTAOFFICIAL"
CHANNEL_LINK = "https://t.me/MagentaFNS"

# Создание бота
bot = telebot.TeleBot(BOT_TOKEN)

# Словарь для временного хранения выбора пользователей
user_choices = {}

# Функция для очистки текста от проблемных символов Markdown
def clean_text(text):
    """Очищает текст от символов которые могут сломать Markdown"""
    if not text:
        return ""
    # Экранируем проблемные символы
    text = re.sub(r'([*_`\[\]()])', r'\\\1', text)
    return text

# База данных для хранения заказов
def init_db():
    try:
        if not os.path.exists('data'):
            os.makedirs('data')
            print("📁 Создана папка data")
        
        conn = sqlite3.connect('data/orders.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                first_name TEXT,
                service_type TEXT,
                description TEXT,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ База данных инициализирована")
        
    except Exception as e:
        print(f"❌ Ошибка создания базы данных: {e}")

# Функция для проверки является ли пользователь админом
def is_admin(user_id):
    return user_id == ADMIN_CHAT_ID

# Функция для отправки уведомления админу
def send_admin_notification(order_id, user_data, service_type, description):
    try:
        service_names = {
            'preview': '🖼 ПРЕВЬЮ',
            'avatar': '👤 АВАТАРКА', 
            'banner': '🎨 БАННЕР',
            'package': '💫 ПАКЕТ "ВСЁ ВКЛЮЧЕНО"'
        }
        
        # Очищаем описание от проблемных символов
        clean_description = clean_text(description)
        
        notification_text = f"""
🎯 *НОВЫЙ ЗАКАЗ* 🎯

*Номер заказа*: #{order_id}
*Услуга*: {service_names.get(service_type, service_type)}
*Время*: {datetime.now().strftime("%d.%m.%Y %H:%M")}

*👤 Информация о клиенте*:
• Имя: {clean_text(user_data.get('first_name', 'Не указано'))}
• Username: @{clean_text(user_data.get('username', 'не указан'))}
• ID: {user_data.get('user_id', 'Не указан')}

*📝 Описание заказа*:
{clean_description}

*🚀 Действия*:
1. Напиши клиенту: @{clean_text(user_data.get('username', 'ID: ' + str(user_data.get('user_id'))))}
2. Уточни детали
3. Приступай к работе
        """
        
        bot.send_message(ADMIN_CHAT_ID, notification_text, parse_mode='Markdown')
        
        # Кнопка для быстрого ответа
        markup = telebot.types.InlineKeyboardMarkup()
        user_id = user_data.get('user_id')
        if user_id:
            reply_btn = telebot.types.InlineKeyboardButton(
                text='💬 Ответить клиенту', 
                url=f'tg://user?id={user_id}'
            )
            markup.add(reply_btn)
        
        bot.send_message(
            ADMIN_CHAT_ID, 
            "⚡ *Быстрая связь с клиентом*", 
            reply_markup=markup, 
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления админу: {e}")

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    
    # Проверяем, является ли пользователь админом
    if is_admin(user.id):
        welcome_text = """
👑 *Привет, Админ* 👑

Это панель управления ботом для заказов дизайна.

*Твои команды*:
📊 /stats - посмотреть статистику
🆔 /myid - узнать свой ID

*Для тестирования заказов используй другой аккаунт*
        """
    else:
        welcome_text = f"""
👋 Привет, {clean_text(user.first_name)}!

Я бот для заказа дизайнерских услуг:
• 🖼 Превью для видео - 50 руб
• 👤 Аватарки - 50 руб  
• 🎨 Баннеры - 50 руб
• 💫 Пакет "Все включено" - 120 руб

Выбери действие ниже 👇
        """
    
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('📋 Услуги и цены')
    btn2 = telebot.types.KeyboardButton('🖼 Посмотреть портфолио')
    btn3 = telebot.types.KeyboardButton('💌 Сделать заказ')
    btn4 = telebot.types.KeyboardButton('📞 Связь с автором')
    markup.add(btn1, btn2, btn3, btn4)
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='Markdown')

# Услуги и цены
@bot.message_handler(func=lambda message: message.text == '📋 Услуги и цены')
def show_services(message):
    services_text = """
🎯 Мои услуги и цены:

🖼 Превью для видео - 50 руб
• Яркое и привлекательное
• С учетом твоей тематики
• Быстрое исполнение

👤 Аватарка - 50 руб  
• Стильная и современная
• Подходящего размера
• В твоем стиле

🎨 Баннер - 50 руб
• Для YouTube, соцсетей
• Качественный дизайн
• Привлекающий внимание

💫 Пакет "Все включено" - 120 руб
• Аватарка + Превью + Баннер
• Выгоднее на 30 руб!
• Единый стиль для всех платформ

💎 Дополнительные услуги:
• Срочный заказ (+50% к стоимости)
• Несколько вариантов на выбор (+30 руб)
• Анимация (+100 руб)
    """
    bot.send_message(message.chat.id, services_text)

# Портфолио
@bot.message_handler(func=lambda message: message.text == '🖼 Посмотреть портфолио')
def show_portfolio(message):
    portfolio_text = f"""
🖼 Мое портфолио:

Посмотри примеры моих работ в моем канале:
{CHANNEL_LINK}

Там ты найдешь:
• Примеры превью
• Стильные аватарки  
• Креативные баннеры

Все работы делаются индивидуально под каждого клиента ✨
    """
    bot.send_message(message.chat.id, portfolio_text)

# Сделать заказ
@bot.message_handler(func=lambda message: message.text == '💌 Сделать заказ')
def start_order(message):
    # Проверяем, является ли пользователь админом
    if is_admin(message.from_user.id):
        bot.send_message(
            message.chat.id, 
            "❌ Вы не можете сделать заказ, так как вы администратор\n\nДля тестирования функционала заказов используйте другой аккаунт."
        )
        return
    
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('🖼 Превью')
    btn2 = telebot.types.KeyboardButton('👤 Аватарка')
    btn3 = telebot.types.KeyboardButton('🎨 Баннер')
    btn4 = telebot.types.KeyboardButton('💫 Пакет "Все включено"')
    btn5 = telebot.types.KeyboardButton('🔙 Назад')
    markup.add(btn1, btn2, btn3, btn4, btn5)
    
    bot.send_message(message.chat.id, "Выбери тип услуги:", reply_markup=markup)

# Обработка выбора услуги
@bot.message_handler(func=lambda message: message.text in ['🖼 Превью', '👤 Аватарка', '🎨 Баннер', '💫 Пакет "Все включено"'])
def handle_service_selection(message):
    # Проверяем, является ли пользователь админом
    if is_admin(message.from_user.id):
        bot.send_message(
            message.chat.id, 
            "❌ Вы не можете сделать заказ, так как вы администратор"
        )
        send_welcome(message)
        return
    
    try:
        service_types = {
            '🖼 Превью': 'preview',
            '👤 Аватарка': 'avatar', 
            '🎨 Баннер': 'banner',
            '💫 Пакет "Все включено"': 'package'
        }
        
        service_type = service_types[message.text]
        
        # Сохраняем выбор пользователя
        user_choices[message.chat.id] = {'service_type': service_type}
        
        msg = bot.send_message(
            message.chat.id, 
            "📝 Опиши, что ты хочешь:\n\n• Тематика\n• Предпочтения по цветам\n• Текст который нужно разместить\n• Любые другие пожелания\n\nМожешь прикрепить пример понравившегося стиля",
            reply_markup=telebot.types.ReplyKeyboardRemove()
        )
        bot.register_next_step_handler(msg, process_order_description)
        
    except Exception as e:
        logger.error(f"Ошибка при выборе услуги: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка. Попробуй еще раз.")
        send_welcome(message)

def process_order_description(message):
    try:
        user_id = message.chat.id
        
        # Проверяем, является ли пользователь админом
        if is_admin(user_id):
            bot.send_message(
                user_id, 
                "❌ Вы не можете сделать заказ, так как вы администратор"
            )
            send_welcome(message)
            return
        
        # Проверяем, есть ли выбор пользователя
        if user_id not in user_choices:
            bot.send_message(user_id, "❌ Сессия устарела. Начни заново с команды /start")
            send_welcome(message)
            return
        
        service_type = user_choices[user_id]['service_type']
        description = message.text
        
        user_data = {
            'user_id': user_id,
            'username': message.from_user.username,
            'first_name': message.from_user.first_name
        }
        
        # Сохраняем заказ в базу данных
        conn = sqlite3.connect('data/orders.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (user_id, username, first_name, service_type, description) 
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, message.from_user.username, message.from_user.first_name, service_type, description))
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        service_names = {
            'preview': '🖼 Превью',
            'avatar': '👤 Аватарка', 
            'banner': '🎨 Баннер',
            'package': '💫 Пакет "Все включено"'
        }
        
        # Очищаем описание для безопасного отображения
        clean_description = clean_text(description)
        clean_username = clean_text(message.from_user.username or 'не указан')
        
        confirm_text = f"""
✅ Заказ принят

Номер заказа: #{order_id}
Услуга: {service_names[service_type]}
Твои пожелания: {clean_description}

📞 Я свяжусь с тобой в течение 1-2 часов для уточнения деталей и оплаты

Твой логин для связи: @{clean_username}

⚡ Скорость исполнения: 1-4 часа
🎨 Качество гарантирую
        """
        
        bot.send_message(user_id, confirm_text)
        
        # Отправляем уведомление админу
        send_admin_notification(order_id, user_data, service_type, description)
        
        logger.info(f"New order #{order_id} from user {user_id}")
        
        # Очищаем временные данные
        if user_id in user_choices:
            del user_choices[user_id]
        
        # Показываем главное меню
        send_welcome(message)
            
    except Exception as e:
        logger.error(f"Error processing order: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при обработке заказа. Попробуй еще раз.")
        # Отправляем без parse_mode чтобы избежать ошибок
        try:
            welcome_text = "Вернуться в главное меню: /start"
            bot.send_message(message.chat.id, welcome_text)
        except:
            pass

# Связь с автором
@bot.message_handler(func=lambda message: message.text == '📞 Связь с автором')
def contact_author(message):
    contact_text = f"""
📞 Связь с автором:

По всем вопросам пиши:
👉 {ADMIN_USERNAME}

Отвечаю быстро 🚀
    """
    bot.send_message(message.chat.id, contact_text)

# Назад в главное меню
@bot.message_handler(func=lambda message: message.text == '🔙 Назад')
def back_to_main(message):
    send_welcome(message)

# Команда для админа - статистика
@bot.message_handler(commands=['stats'])
def send_stats(message):
    if message.from_user.id == ADMIN_CHAT_ID:
        try:
            conn = sqlite3.connect('data/orders.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM orders')
            total_orders = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM orders WHERE DATE(created_at) = DATE("now")')
            today_orders = cursor.fetchone()[0]
            
            cursor.execute('SELECT service_type, COUNT(*) FROM orders GROUP BY service_type')
            service_stats = cursor.fetchall()
            
            stats_text = f"""
📊 Статистика бота

📈 Всего заказов: {total_orders}
🎯 За сегодня: {today_orders}

📋 По услугам:
"""
            for service_type, count in service_stats:
                service_name = {
                    'preview': '🖼 Превью',
                    'avatar': '👤 Аватарки',
                    'banner': '🎨 Баннеры',
                    'package': '💫 Пакеты'
                }.get(service_type, service_type)
                stats_text += f"{service_name}: {count}\n"
            
            conn.close()
            bot.send_message(message.chat.id, stats_text)
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            bot.send_message(message.chat.id, f"Ошибка получения статистики: {e}")
    else:
        bot.send_message(message.chat.id, "❌ Эта команда только для администратора")

# Команда для получения ID
@bot.message_handler(commands=['myid'])
def show_my_id(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username
    
    # Проверяем, является ли пользователь админом
    if is_admin(user_id):
        role_text = "👑 Вы администратор"
    else:
        role_text = "👤 Вы клиент"
    
    response_text = f"""
👤 Твой профиль:

{role_text}
ID: {user_id}
Имя: {clean_text(first_name)}
Username: @{clean_text(username or 'не указан')}

📋 Скопируй свой ID: {user_id}
    """
    
    bot.send_message(message.chat.id, response_text)

# Обработка любых других сообщений
@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    if message.text not in ['📋 Услуги и цены', '🖼 Посмотреть портфолио', '💌 Сделать заказ', '📞 Связь с автором', '🔙 Назад']:
        bot.send_message(message.chat.id, "🤔 Не понимаю команду. Используй кнопки меню или /start")

# Функция для проверки работоспособности бота
def check_bot_health():
    try:
        bot_info = bot.get_me()
        logger.info(f"Бот активен: @{bot_info.username}")
        return True
    except Exception as e:
        logger.error(f"Ошибка подключения бота: {e}")
        return False

# Запуск бота
if __name__ == "__main__":
    print("🤖 Бот запускается...")
    print(f"👑 Админ: {ADMIN_USERNAME}")
    print(f"🆔 ID админа: {ADMIN_CHAT_ID}")
    print(f"📢 Канал: {CHANNEL_LINK}")
    
    if not os.path.exists('data'):
        os.makedirs('data')
        print("📁 Создана папка data")
    
    init_db()
    
    if check_bot_health():
        print("✅ Бот успешно подключен к Telegram")
        print("🚀 Бот запущен и готов к работе!")
        print("📞 Уведомления будут приходить админу в личку")
        
        try:
            startup_text = f"""
🤖 Бот успешно запущен
👑 Владелец: {ADMIN_USERNAME}
📢 Канал: {CHANNEL_LINK}
🔒 Режим администратора активирован
🎯 Ожидаю новые заказы
            """
            bot.send_message(ADMIN_CHAT_ID, startup_text)
        except Exception as e:
            print(f"⚠️ Не удалось отправить уведомление админу: {e}")
        
        while True:
            try:
                print("🔄 Запуск опроса...")
                bot.infinity_polling(timeout=60, long_polling_timeout=30)
            except Exception as e:
                logger.error(f"Ошибка опроса: {e}")
                print(f"🔄 Перезапуск через 10 секунд... Ошибка: {e}")
                time.sleep(10)
    else:
        print("❌ Не удалось подключить бота. Проверь токен.")