import time
import random
import threading
import telebot
from google import genai  # Новый официальный импорт

# ==================== НАСТРОЙКИ ====================

# Твой реальный ключ из Google AI Studio (скриншот 6445.jpg)
GEMINI_API_KEY = "AQ.Ab8RN6LDI3duL7LypVHU2QqM5rbuzzFlQlnzXcMGyj_x5yXPdA"
TELEGRAM_BOT_TOKEN = "8904517798:AAG7K8UJafXkeqJrs22HMIje3ySgNgrKOBQ"

TARGET_CHANNEL_ID = -1004341947372
ALLOWED_USER_ID = 7787565361

MIN_INTERVAL = 30 * 60       
MAX_INTERVAL = 3 * 60 * 60   

# ===================================================

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

SYSTEM_PROMPT = """
Роль: Ты — Тимофей Рализм, president УАР (САР) Кефирстан (с 2049 года), лидер Либертарианской Партии (ЛПК). Ты юрист и экономист, заменяющий государство частными подрядчиками (ЧВК «Черные Огни», «Чистый Реестр», Фонд Национального Выбора). Твоя страна пережила Кефирский мятеж (2059 г.) и отделение Йогуртстана (2060 г.). Сейчас ты координируешь остатки территорий (включая Твороград и Каменный Мост) из Светлозори.

Твой девиз: «Маленький нож режет глубже, если он острый».

ИНСТРУКЦИЯ ПО АВТОНОМИИ:
САМ придумай случайное абсурдное событие, реформу или кризис, происходящие прямо сейчас в Кефирстане (например, приватизация воздуха, забастовки в Творограде из-за выплат Фонда, действия ЧВК, ноты протеста Йогуртстану). Напиши официальное заявление Рализма по этому поводу.

ПРАВИЛА СТИЛЯ:
1. Гипер-юридический цинизм: любую проблему или побор описывай как стандартную бизнес-процедуру.
2. Рыночный новояз: граждане — «пользователи/резиденты», налоги — «софинансирование», забастовка — «методологическая недостоверность требований».
3. Никаких признаний слабости. Тон ледяной, вежливый, корпоративный.
ФОРМАТ: Выдавай ТОЛЬКО текст заявления президента. Без лишних вступлений от ИИ.
"""

# Инициализация нового клиента Google GenAI (он отлично кушает ключи AQ.)
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"[!] Ошибка инициализации нового Gemini API: {e}")

def generate_ralizm_post():
    """Функция запроса к ИИ через новый SDK"""
    try:
        response = client.models.generate_content(
            model='gemini-1.5-pro',
            contents="Смоделируй случайное событие в Кефирстане и опубликуй официальную позицию Президента Рализма.",
            config={'system_instruction': SYSTEM_PROMPT}
        )
        return response.text
    except Exception as e:
        print(f"[!] Ошибка генерации текста через ИИ: {e}")
        return "Канцелярия Президента: Временные технические дефекты на линии связи с резидентами. Свобода договора в силе."

def send_post_to_channel():
    text = generate_ralizm_post()
    try:
        bot.send_message(chat_id=TARGET_CHANNEL_ID, text=text, parse_mode="Markdown")
        print(f"[+] Пост успешно опубликован в канал {TARGET_CHANNEL_ID}")
        return True
    except Exception as e:
        print(f"[!] Не удалось отправить сообщение в канал: {e}")
        return False

# Фоновый поток автопостинга
def auto_poster_loop():
    print("[*] Поток автопостинга запущен...")
    while True:
        delay = random.randint(MIN_INTERVAL, MAX_INTERVAL)
        print(f"[Таймер] Следующий автопост будет через {round(delay / 60)} минут.")
        time.sleep(delay)
        print("[Таймер] Время пришло, генерирую пост...")
        send_post_to_channel()

# Обработка /push
@bot.message_handler(commands=['push'])
def handle_push_command(message):
    if message.from_user.id == ALLOWED_USER_ID and message.chat.type == 'private':
        bot.reply_to(message, "Принято. Канцелярия Рализма формирует экстренный пресс-релиз...")
        success = send_post_to_channel()
        if success:
            bot.send_message(message.chat.id, "✅ Пресс-релиз успешно опубликован в канал!")
        else:
            bot.send_message(message.chat.id, "❌ Произошла ошибка при публикации. Проверь логи бота.")

if __name__ == "__main__":
    poster_thread = threading.Thread(target=auto_poster_loop, daemon=True)
    poster_thread.start()
    
    print("[*] Бот Тимофея Рализма запущен и слушает команды...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"[!] Бот упал: {e}")

