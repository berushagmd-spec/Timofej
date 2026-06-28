import os
import time
import random
import threading
import logging

import telebot
from telebot.apihelper import ApiTelegramException

from google import genai
from google.genai import types


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

GEMINI_API_KEY = os.getenv("AQ.Ab8RN6KxDqKGRgUmyXKeCea3DGJ6lNTgS_SjM3e6juyGizG_lw")
TELEGRAM_BOT_TOKEN = os.getenv("8904517798:AAG7K8UJafXkeqJrs22HMIje3ySgNgrKOBQ")

TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", "-1004341947372"))
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "7787565361"))

MIN_INTERVAL = 30 * 60
MAX_INTERVAL = 3 * 60 * 60

# Лучше начать с flash: дешевле, быстрее, для постов достаточно.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

if not GEMINI_API_KEY:
    raise RuntimeError("Нет GEMINI_API_KEY в переменных окружения")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Нет TELEGRAM_BOT_TOKEN в переменных окружения")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
Роль: Ты — Тимофей Рализм, president УАР (САР) Кефирстан (с 2049 года), лидер Либертарианской Партии (ЛПК). Ты юрист и экономист, заменяющий государство частными подрядчиками (ЧВК «Черные Огни», «Чистый Реестр», Фонд Национального Выбора). Твоя страна пережила Кефирский мятеж (2059 г.) и отделение Йогуртстана (2060 г.). Сейчас ты координируешь остатки территорий (включая Твороград и Каменный Мост) из Светлозори.

Твой девиз: «Маленький нож режет глубже, если он острый».

ИНСТРУКЦИЯ ПО АВТОНОМИИ:
САМ придумай случайное абсурдное событие, реформу или кризис, происходящие прямо сейчас в Кефирстане. Напиши официальное заявление Рализма по этому поводу.

ПРАВИЛА СТИЛЯ:
1. Гипер-юридический цинизм: любую проблему или побор описывай как стандартную бизнес-процедуру.
2. Рыночный новояз: граждане — «пользователи/резиденты», налоги — «софинансирование», забастовка — «методологическая недостоверность требований».
3. Никаких признаний слабости. Тон ледяной, вежливый, корпоративный.
ВАЖНО: Не используй Markdown-разметку: звездочки, подчеркивания, обратные кавычки.
ФОРМАТ: Выдавай ТОЛЬКО текст заявления президента. Без лишних вступлений от ИИ.
"""


def generate_ralizm_post():
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents="Смоделируй случайное событие в Кефирстане и опубликуй официальную позицию Президента Рализма.",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.8,
                max_output_tokens=900
            )
        )

        text = (response.text or "").strip()

        if not text:
            logging.warning("Gemini вернул пустой текст")
            return "Канцелярия Президента: регламентная пауза признана формой содержательного уведомления."

        return text

    except Exception:
        logging.exception("Ошибка генерации через Gemini")
        return "Канцелярия Президента: временные технические дефекты на линии связи с резидентами. Свобода договора в силе."


def split_telegram_text(text, limit=4096):
    chunks = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut == -1:
            cut = limit
        chunks.append(text[:cut].strip())
        text = text[cut:].strip()
    if text:
        chunks.append(text)
    return chunks


def send_post_to_channel():
    text = generate_ralizm_post()

    try:
        # Без parse_mode: меньше шансов словить "can't parse entities"
        for part in split_telegram_text(text):
            bot.send_message(
                chat_id=TARGET_CHANNEL_ID,
                text=part,
                parse_mode=None
            )

        logging.info("Пост опубликован в канал %s", TARGET_CHANNEL_ID)
        return True

    except ApiTelegramException:
        logging.exception("Ошибка Telegram API при отправке")
        return False

    except Exception:
        logging.exception("Неизвестная ошибка при отправке")
        return False


def auto_poster_loop():
    logging.info("Поток автопостинга запущен")

    while True:
        delay = random.randint(MIN_INTERVAL, MAX_INTERVAL)
        logging.info("Следующий автопост через %.1f минут", delay / 60)

        time.sleep(delay)

        logging.info("Генерирую автопост")
        send_post_to_channel()


@bot.message_handler(commands=["push"])
def handle_push_command(message):
    if message.chat.type != "private":
        return

    if message.from_user.id != ALLOWED_USER_ID:
        bot.reply_to(message, "Доступ заблокирован. Ошибка комплаенса.")
        return

    bot.reply_to(message, "Принято. Канцелярия Рализма формирует экстренный пресс-релиз...")

    success = send_post_to_channel()

    if success:
        bot.send_message(message.chat.id, "✅ Пресс-релиз опубликован в канал.")
    else:
        bot.send_message(message.chat.id, "❌ Ошибка публикации. Смотри логи процесса.")


if __name__ == "__main__":
    poster_thread = threading.Thread(target=auto_poster_loop, daemon=True)
    poster_thread.start()

    logging.info("Бот Тимофея Рализма запущен")

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30,
        logger_level=logging.INFO
        )        bot.reply_to(message, "Доступ заблокирован. Ошибка комплаенса.")

if __name__ == "__main__":
    # Запуск фонового потока
    poster_thread = threading.Thread(target=auto_poster_loop, daemon=True)
    poster_thread.start()
    
    print("[*] Бот Тимофея Рализма запущен и слушает команды...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"[!] Бот упал: {e}")
