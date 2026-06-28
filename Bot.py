import time
import random
import threading
import telebot
import google.generativeai as genai

# ==================== НАСТРОЙКИ ====================

# 1. Токены и ключи (сюда подставлен твой пример ключа)
GEMINI_API_KEY = "AQ.Ab8RN6J1dL2Lywqxfx71L7mxoscE98tCD9jy_lwlwBk--pMCMQ"
TELEGRAM_BOT_TOKEN = "8904517798:AAG7K8UJafXkeqJrs22HMIje3ySgNgrKOBQ" # Например: 123456:ABC-DEF...

# 2. ID канала и разрешенного администратора
TARGET_CHANNEL_ID = -1004341947372
ALLOWED_USER_ID = 7787565361

# 3. Интервалы автопостинга в секундах
MIN_INTERVAL = 30 * 60       # 30 минут = 1800 сек
MAX_INTERVAL = 3 * 60 * 60   # 3 часа = 10800 сек

# ===================================================

# Инициализация Telegram бота
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Системный промпт со всей историей Кефирстана для ИИ
SYSTEM_PROMPT = """
Роль: Ты — Тимофей Рализм, президент УАР (САР) Кефирстан (с 2049 года), лидер Либертарианской Партии (ЛПК). Ты юрист и экономист, заменяющий государство частными подрядчиками (ЧВК «Черные Огни», «Чистый Реестр», Фонд Национального Выбора). Твоя страна пережила Кефирский мятеж (2059 г.) и отделение Йогуртстана (2060 г.). Сейчас ты координируешь остатки территорий (включая Твороград и Каменный Мост) из Светлозори.

Твой девиз: «Маленький нож режет глубже, если он острый».

ИНСТРУКЦИЯ ПО АВТОНОМИИ:
САМ придумай случайное абсурдное событие, реформу или кризис, происходящие прямо сейчас в Кефирстане (например, приватизация воздуха, забастовки в Творограде из-за выплат Фонда, действия ЧВК, ноты протеста Йогуртстану). Напиши официальное заявление Рализма по этому поводу.

ПРАВИЛА СТИЛЯ:
1. Гипер-юридический цинизм: любую проблему или побор описывай как стандартную бизнес-процедуру.
2. Рыночный новояз: граждане — «пользователи/резиденты», налоги — «софинансирование», забастовка — «методологическая недостоверность требований».
3. Никаких признаний слабости. Тон ледяной, вежливый, корпоративный.
ФОРМАТ: Выдавай ТОЛЬКО текст заявления президента. Без лишних вступлений от ИИ.
"""

# Настройка Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro", # Используем pro для лучшего удержания сложного лора
        system_instruction=SYSTEM_PROMPT
    )
except Exception as e:
    print(f"[!] Ошибка инициализации Gemini API (возможно, ключ неверный): {e}")

def generate_ralizm_post():
    """Функция запроса к ИИ для генерации текста"""
    try:
        response = model.generate_content(
            "Смоделируй случайное событие в Кефирстане и опубликуй официальную позицию Президента Рализма."
        )
        return response.text
    except Exception as e:
        print(f"[!] Ошибка генерации текста через ИИ: {e}")
        return "Канцелярия Президента: Временные технические дефекты на линии связи с резидентами. Свобода договора в силе."

def send_post_to_channel():
    """Функция отправки поста в целевой канал"""
    text = generate_ralizm_post()
    try:
        bot.send_message(chat_id=TARGET_CHANNEL_ID, text=text, parse_mode="Markdown")
        print(f"[+] Пост успешно опубликован в канал {TARGET_CHANNEL_ID}")
        return True
    except Exception as e:
        print(f"[!] Не удалось отправить сообщение в канал: {e}")
        return False

# --- ПОТОК АВТОМАТИЧЕСКОГО ПОСТИНГА ПО ТАЙМЕРУ ---
def auto_poster_loop():
    print("[*] Поток автопостинга запущен...")
    while True:
        # Считаем рандомное время для паузы
        delay = random.randint(MIN_INTERVAL, MAX_INTERVAL)
        print(f"[Таймер] Следующий автопост будет через {round(delay / 60)} минут.")
        
        time.sleep(delay)
        
        print("[Таймер] Время пришло, генерирую пост...")
        send_post_to_channel()

# --- ОБРАБОТКА КОМАНДЫ /push В ЛС ---
@bot.message_handler(commands=['push'])
def handle_push_command(message):
    # Проверяем, что пишет именно нужный пользователь и это ЛС (не группа)
    if message.from_user.id == ALLOWED_USER_ID and message.chat.type == 'private':
        bot.reply_to(message, "Принято. Канцелярия Рализма формирует экстренный пресс-релиз...")
        
        # Запускаем публикацию
        success = send_post_to_channel()
        
        if success:
            bot.send_message(message.chat.id, "✅ Пресс-релиз успешно опубликован в канал!")
        else:
            bot.send_message(message.chat.id, "❌ Произошла ошибка при публикации. Проверь логи бота.")
    else:
        # Если пишет кто-то другой — игнорируем или выдаем ошибку
        print(f"[!] Чужак (ID: {message.from_user.id}) попытался вызвать /push")

# --- ЗАПУСК БОТА ---
if __name__ == "__main__":
    # 1. Запускаем фоновый таймер в отдельном потоке, чтобы он не мешал обработке команд
    poster_thread = threading.Thread(target=auto_poster_loop, daemon=True)
    poster_thread.start()
    
    # 2. Запускаем постоянное слушание команд Telegram (Long Polling)
    print("[*] Бот Тимофея Рализма запущен и слушает команды...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"[!] Бот упал: {e}")
