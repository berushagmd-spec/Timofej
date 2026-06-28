import time
import random
import threading
import telebot
from google import genai
from google.genai import types  # Необходим для правильного конфига ИИ

# ==================== НАСТРОЙКИ ====================
GEMINI_API_KEY = "AQ.Ab8RN6KxDqKGRgUmyXKeCea3DGJ6lNTgS_SjM3e6juyGizG_lw"
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
ВАЖНО: Постарайся не злоупотреблять спецсимволами разметки (вроде *, _, `), пиши структурировано.
ФОРМАТ: Выдавай ТОЛЬКО текст заявления президента. Без лишних вступлений от ИИ.
"""

# Инициализируем клиент глобально, чтобы избежать NameError
client = None
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
    print("[+] Клиент Gemini успешно инициализирован.")
except Exception as e:
    print(f"[!] Критическая ошибка инициализации Gemini API: {e}")

def generate_ralizm_post():
    """Функция запроса к ИИ через новый SDK"""
    if client is None:
        return "Канцелярия Президента: Ошибка авторизации системы ИИ. Проверьте API ключ."
        
    try:
        # Корректный вызов для google-genai v1+
        response = client.models.generate_content(
            model='gemini-1.5-pro',
            contents="Смоделируй случайное событие в Кефирстане и опубликуй официальную позицию Президента Рализма.",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.8  # Добавим немного креативности для абсурдных законов
            )
        )
        return response.text
    except Exception as e:
        print(f"[!] Ошибка генерации текста через ИИ: {e}")
        return "Канцелярия Президента: Временные технические дефекты на линии связи с резидентами. Свобода договора в силе."

def send_post_to_channel():
    text = generate_ralizm_post()
    try:
        # Пробуем отправить с красивой разметкой
        bot.send_message(chat_id=TARGET_CHANNEL_ID, text=text, parse_mode="Markdown")
        print(f"[+] Пост успешно опубликован в канал {TARGET_CHANNEL_ID}")
        return True
    except telebot.apihelper.ApiTelegramException as te:
        # Если сломалось из-за разметки Markdown, отправляем чистый текст
        if "can't parse entities" in str(te).lower():
            print("[!] Ошибка разметки Telegram. Отправляю пост без Markdown форматирования...")
            try:
                bot.send_message(chat_id=TARGET_CHANNEL_ID, text=text, parse_mode=None)
                return True
            except Exception as e:
                print(f"[!] Даже без разметки не ушло: {e}")
                return False
        else:
            print(f"[!] Ошибка API Telegram: {te}")
            return False
    except Exception as e:
        print(f"[!] Неизвестная ошибка при отправке: {e}")
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
            bot.send_message(message.chat.id, "❌ Произошла ошибка при публикации. Проверь консоль бота.")
    else:
        bot.reply_to(message, "Доступ заблокирован. Ошибка комплаенса.")

if __name__ == "__main__":
    # Запуск фонового потока
    poster_thread = threading.Thread(target=auto_poster_loop, daemon=True)
    poster_thread.start()
    
    print("[*] Бот Тимофея Рализма запущен и слушает команды...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"[!] Бот упал: {e}")
