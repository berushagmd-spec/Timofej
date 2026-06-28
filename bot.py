import os
import asyncio
import logging
from textwrap import dedent

from dotenv import load_dotenv
from google import genai
from google.genai import types

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
CHANNEL_ID = os.getenv("CHANNEL_ID")
DEFAULT_STYLE = os.getenv("DEFAULT_STYLE", "toilet").lower().strip()

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Нет TELEGRAM_BOT_TOKEN в .env")

if not GEMINI_API_KEY:
    raise RuntimeError("Нет GEMINI_API_KEY в .env")


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)

client = genai.Client(api_key=GEMINI_API_KEY)


BASE_LORE = dedent("""
Ты пишешь ПАРОДИЙНЫЕ заявления вымышленного политика Тимофея Рализма
для сатирического Telegram-канала. Это не реальный политик, не официальный канал
и не настоящий документ. Это художественная политическая сатира.

Кто такой Рализм в этой пародии:
- Президент Кефирстана, холодный юридический хищник в костюме.
- Любимые слова: договор, контракт, порядок, участие, ответственность, процедура,
  конституционный контур, гражданское софинансирование, Фонд Национального Выбора.
- Идеологически он говорит про минимальное государство, свободу договора, низкие налоги,
  частную инициативу и ответственность.
- На практике любой провал он объясняет тем, что граждане "неправильно поняли свободу".
- Он не говорит "побор". Он говорит "добровольное участие".
- Он не говорит "нас кроют матом". Он говорит "общество находится в стадии эмоционального аудита".
- Он не говорит "всех нахуй". Он говорит "лица, отказавшиеся от договора, могут проследовать в процедурный унитаз истории".

Правила безопасности:
- Не изображай это как реальное заявление реального правительства.
- Не призывай к реальному насилию, травле, незаконным действиям или преследованию людей.
- Можно материться и быть грубым, но это должна быть комедийная политическая пародия.
- Не атакуй реальные защищенные группы. Ругай абстрактных чиновников, вымышленных оппонентов,
  бюрократию, Фонд, процедуру, договорную гниль, городскую канализацию и политический абсурд.
""")


STYLE_PROMPTS = {
    "normal": dedent("""
    Стиль: холодное официальное заявление.
    Маты не используй. Рофл минимальный. 2-4 абзаца.
    Звучит как юрист, который продал душу частному арбитражу.
    """),

    "rofl": dedent("""
    Стиль: угарная Telegram-пародия.
    Можно использовать маты, но не через каждое слово.
    Должно быть смешно: бюрократический канцелярит + внезапная грязная метафора.
    Примеры тона:
    - "Это не побор, это добровольный финансовый подзатыльник зрелости."
    - "Кто не вошел в договор, тот не должен удивляться, что дверь открылась в сортир."
    2-5 абзацев.
    """),

    "toilet": dedent("""
    Стиль: всё в унитаз.
    Больше унитазной метафорики, канализации, очистных, смыва, говна, договорной вони.
    Маты разрешены, но текст должен оставаться похожим на официальный пост Рализма.
    Он матерится не как школьник, а как президент-юрист, которого прорвало.
    Обязательно 1 раз используй образ "унитаза истории" или "процедурного унитаза".
    3-5 абзацев.
    """),

    "max": dedent("""
    Стиль: максимально ебанутая сатирическая версия.
    Канцелярит + истеричный официальный рофл + маты + унитазная философия.
    Текст должен звучать так, будто пресс-служба Рализма три дня не спала,
    нюхала мокрую бухгалтерию Фонда и решила объявить народу юридический апокалипсис.
    Можно использовать слова: нахуй, хуйня, пиздец, говно, жопа, сраный, ебаный.
    Но не превращай текст в бессмысленную ругань: каждая грязная фраза должна работать на образ.
    3-6 абзацев.
    """),
}


def normalize_style(style: str) -> str:
    style = (style or DEFAULT_STYLE or "toilet").lower().strip()
    if style not in STYLE_PROMPTS:
        return "toilet"
    return style


def get_user_style(context: ContextTypes.DEFAULT_TYPE) -> str:
    return normalize_style(context.user_data.get("style", DEFAULT_STYLE))


def build_prompt(topic: str, style: str) -> str:
    return dedent(f"""
    {BASE_LORE}

    {STYLE_PROMPTS[style]}

    Напиши пародийный пост Тимофея Рализма для личного Telegram-канала.

    Инфоповод:
    {topic}

    Требования:
    - Не ставь заголовок, если он не нужен.
    - Не объясняй, что это пародия, внутри самого поста.
    - Не добавляй дисклеймер в конце.
    - Сохрани узнаваемую смесь: договор, Фонд, свобода выбора, процедура, холодная наглость.
    - Финальная фраза должна быть ударной и мемной.
    """)


def generate_ralizm_post(topic: str, style: str) -> str:
    prompt = build_prompt(topic=topic, style=style)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=1.05 if style in {"toilet", "max"} else 0.85,
            top_p=0.95,
            max_output_tokens=1100,
        ),
    )

    text = (response.text or "").strip()

    if not text:
        return "Генератор молчит. Видимо, Фонд снова не оплатил речевой контур."

    return text


def split_telegram_text(text: str, limit: int = 3900) -> list[str]:
    chunks = []

    while len(text) > limit:
        cut = text.rfind("\n\n", 0, limit)
        if cut == -1:
            cut = text.rfind(" ", 0, limit)
        if cut == -1:
            cut = limit

        chunks.append(text[:cut].strip())
        text = text[cut:].strip()

    if text:
        chunks.append(text)

    return chunks


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    style = get_user_style(context)

    await update.message.reply_text(
        "Я Рализм-рофлобот: договор, Фонд, канцелярит, унитаз истории.\n\n"
        "Просто напиши инфоповод, и я сделаю пост.\n\n"
        "Команды:\n"
        "/post тема — сгенерировать пост\n"
        "/publish тема — сгенерировать и отправить в канал\n"
        "/style normal — сухой официоз\n"
        "/style rofl — рофл с матами\n"
        "/style toilet — всё в унитаз\n"
        "/style max — максимально ебанутый режим\n"
        "/examples — примеры тем\n\n"
        f"Текущий стиль: {style}"
    )


async def examples(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Примеры тем:\n\n"
        "• рабочие очистной станции отказались платить добровольный взнос\n"
        "• депутаты требуют аудит Фонда Национального Выбора\n"
        "• трамваи встали и водитель написал на табло «едем к совести»\n"
        "• медсестры вынесли список детей без лекарств\n"
        "• оппозиция назвала программу гражданского участия побором\n"
        "• граждане спрашивают, почему свобода договора пахнет канализацией"
    )


async def style_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "Выбери стиль: normal, rofl, toilet, max\n"
            f"Сейчас: {get_user_style(context)}"
        )
        return

    style = normalize_style(context.args[0])
    context.user_data["style"] = style

    await update.message.reply_text(f"Стиль включен: {style}")


async def make_post(update: Update, context: ContextTypes.DEFAULT_TYPE, topic: str) -> str | None:
    topic = (topic or "").strip()

    if not topic:
        await update.message.reply_text("Дай инфоповод. Например: /post рабочие отказались платить в Фонд")
        return None

    style = get_user_style(context)
    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        text = await asyncio.to_thread(generate_ralizm_post, topic, style)
    except Exception as e:
        logging.exception("Gemini generation failed")
        await update.message.reply_text(f"Генератор упал в процедурный унитаз: {e}")
        return None

    return text


async def post_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    topic = " ".join(context.args)
    text = await make_post(update, context, topic)
    if text is None:
        return

    for chunk in split_telegram_text(text):
        await update.message.reply_text(chunk)


async def publish_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not CHANNEL_ID:
        await update.message.reply_text(
            "CHANNEL_ID не задан в .env. Добавь туда, например: CHANNEL_ID=@your_channel"
        )
        return

    topic = " ".join(context.args)
    text = await make_post(update, context, topic)
    if text is None:
        return

    for chunk in split_telegram_text(text):
        await context.bot.send_message(chat_id=CHANNEL_ID, text=chunk)

    await update.message.reply_text("Опубликовано. Пост проследовал в канал по договорной трубе.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    text = await make_post(update, context, update.message.text)
    if text is None:
        return

    for chunk in split_telegram_text(text):
        await update.message.reply_text(chunk)


def main() -> None:
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("examples", examples))
    app.add_handler(CommandHandler("style", style_command))
    app.add_handler(CommandHandler("post", post_command))
    app.add_handler(CommandHandler("publish", publish_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Ralizm ROFL bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
