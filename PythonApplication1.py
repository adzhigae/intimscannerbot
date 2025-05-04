import asyncio
import os
import requests
import json
import random
import threading



from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import URLInputFile
from aiogram.types import BotCommand
from aiohttp import web


AGREEMENT_LINK = "https://telegra.ph/Polzovatelskoe-soglashenie-IntimScannerBot-05-03"


from stats import update_user_stat, get_global_stats, get_all_user_stats

# ========================== БЛОК 1: Импорты и настройка окружения ==========================

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")  # Ваш токен от Telegram бота

# Инициализируем объект бота с HTML-разметкой и диспетчер
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# ========================== БЛОК: Подключение шаблонов из файла ==========================

# Загружаем шаблоны из templates.json
with open("templates.json", "r", encoding="utf-8") as file:
    TEMPLATES = json.load(file)

# Отслеживание использованных шаблонов пользователем
used_templates = {}

def get_unique_template(user_id: int, trait: str) -> str:
    all_templates = TEMPLATES.get(trait, [])
    used = used_templates.get(user_id, {}).get(trait, [])

    available = [t for i, t in enumerate(all_templates) if i not in used]

    if not available:
        # Всё показано — сбрасываем
        used_templates[user_id][trait] = []
        available = all_templates[:]

    selected = random.choice(available)
    selected_index = all_templates.index(selected)

    if user_id not in used_templates:
        used_templates[user_id] = {}
    if trait not in used_templates[user_id]:
        used_templates[user_id][trait] = []

    used_templates[user_id][trait].append(selected_index)

    return selected

# Заголовки кнопок для выбора анализа
BUTTON_TITLES = {
    "lust": "💋 О чём мечтает ночью",
    "money": "💎 Важны ли деньги?",
    "power": "🎯 Поддается ли доминированию?"
}



# Основной промо-текст, который показывается при команде /start
PROMO_TEXT = """🧠 Учёные доказали: существует 300+ типов внешности, отражающих поведение.

Ты узнаешь:
• Насколько она склонна к флирту 😏  
• Стоит ли тратить на неё время ⌛️
• Как разжечь между вами искру ❤️‍🔥

🤖 Я умею:
📸 Делать AI-анализ по одному фото
💬 Предсказать поведение в общении и близости
💰 Распознать интерес к статусу или выгоде
🗝 И узнать на основе данных как её добиться

Просто пришли фото девушки — и я всё расскажу. Анонимно, быстро, без лишних слов😈"""

# Текст с описанием проекта и отказом от ответственности (/about)
DISCLAIMER = """👨‍⚖️ <b>О проекте и отказ от ответственности</b>

<b>IntimScannerBot</b> — это развлекательный Telegram-бот, использующий нейросетевой генератор для создания флиртовых описаний по загруженному изображению.

<b>❗Дисклеймер:</b>  
• Все описания — художественные фантазии, не отражающие реальность.  
• Бот не даёт реальных оценок личности, поведения или внешности.  
• Все изображения обрабатываются анонимно и не сохраняются.  
• Использование бота — добровольное. Ответы не являются советом или фактом.  
• Бот не нарушает политику Telegram или OpenAI и не содержит NSFW.

💬 Проект создан для развлечения, с уважением к приватности и этике."""

# Словарь для хранения промежуточных данных по пользователям
user_data = {}

# ========================== БЛОК 2: Переменные, шаблоны и кнопки ==========================

MENU_MARKUP = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=BUTTON_TITLES["lust"], callback_data="lust")],
        [InlineKeyboardButton(text=BUTTON_TITLES["money"], callback_data="money")],
        [InlineKeyboardButton(text=BUTTON_TITLES["power"], callback_data="power")]
    ]
)
# ========================== БЛОК 3: Обработчик команды /start ==============================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    cid = message.chat.id

    if cid not in user_data:
        user_data[cid] = {}

    # Показываем соглашение, если ещё не принято
    if not user_data[cid].get("agreement_accepted"):
        agreement_text = (
            f"Для начала работы с ботом, необходимо ознакомиться с "
            f"<a href='{AGREEMENT_LINK}'>пользовательским соглашением</a>\n\n"
            f"⚠️ Нажимая кнопку «Я согласен», вы подтверждаете, что "
            f"ознакомились с пользовательским соглашением и принимаете его условия!"
        )

        agree_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Я Согласен", callback_data="agree_terms")]
        ])

        await message.answer(agreement_text, reply_markup=agree_kb, disable_web_page_preview=False)
        return

    # Если уже согласился — промо и напоминалка
    update_user_stat(cid)

    if not user_data[cid].get("promo_sent"):
        await message.answer(PROMO_TEXT)
        user_data[cid]["promo_sent"] = True

        async def reminder():
            await asyncio.sleep(90)
            if 'photo_id' not in user_data.get(cid, {}):
                try:
                    await bot.send_message(cid, "📸 Не забудь — просто пришли фото девушки...")
                except:
                    pass

        asyncio.create_task(reminder())

    if user_data[cid].get("photo_id"):
        await message.answer("Выбери тип анализа 👇", reply_markup=MENU_MARKUP)

    # Уведомление админа о новом пользователе (один раз)
    if not user_data[cid].get("notified_admin"):
        try:
            await bot.send_message(ADMIN_ID, f"🆕 Новый пользователь: @{message.from_user.username} (ID: {cid})")
            user_data[cid]["notified_admin"] = True
        except:
            pass

    # Подсказка для пользователя: отправить фото
    await message.answer("📌 Просто отправь фото девушки. Я предложу выбрать один из типов анализа. Всё анонимно и бесплатно 😉")




# ========================== БЛОК 8: Кнопка 'Загрузить новое фото' ==========================

@dp.message(F.photo)
async def handle_photo(message: Message):
    cid = message.chat.id  # ID чата
    fid = message.photo[-1].file_id  # ID файла фото

    if not user_data.get(cid, {}).get("agreement_accepted"):
        await message.answer("⚠️ Чтобы продолжить, нажмите кнопку «✅ Я согласен» в пользовательском соглашении выше.")
        return



    # Если пользователь отправил то же фото дважды — предупредить
    if cid in user_data and user_data[cid].get('photo_id') == fid:
        await message.answer("🔁 Это фото уже анализировалось. Отправь новое.")
        return

    # Скачиваем фото с серверов Telegram
    file = await bot.get_file(fid)
    img_bytes = requests.get(f"https://api.telegram.org/file/bot{API_TOKEN}/{file.file_path}").content

    # Проверяем, что на фото именно женское лицо
    if not await is_female_face(img_bytes):
        await message.answer("⚠️ Нужно чёткое фото девушки (одно лицо, без искажений). Попробуй другое.")
        return

    # Сохраняем данные пользователя и предлагаем меню анализа
    user_data[cid] = {'photo_id': fid, 'analyzed': {}, 'menu_msg_id': None}
    update_user_stat(cid, "photo")  # лог фото

    msg = await message.answer("Фото получено ✅ Выбери тип анализа 👇", reply_markup=MENU_MARKUP)
    user_data[cid]['menu_msg_id'] = msg.message_id

# ========================== БЛОК 9: Кнопка 'Повторить анализ' ==============================

@dp.callback_query(F.data == "get_instruction")
async def handle_get_instruction(call: CallbackQuery):
    cid = call.message.chat.id

    if user_data.get(cid, {}).get("instruction_shown"):
        # Уже показано — просто не реагируем
        return

    text = (
        "🔓 <b>Инструкция — это не просто список. Это пошаговый сценарий, как довести до настоящей искры.</b>\n"
        "Ты поймёшь, когда включиться, когда отступить — и как действовать, чтобы остаться в голове надолго.\n\n"
        "✅ Готов начать? Нажми кнопку ниже и получи всё."
    )

    final_payment_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Готов, покажи инструкцию", callback_data="show_payment")
    ]])

    await call.message.edit_text(text, reply_markup=final_payment_kb)



@dp.callback_query(F.data == "show_payment")
async def handle_show_payment(call: CallbackQuery):
    cid = call.message.chat.id

    # Если уже была показана инструкция после оплаты — ничего не делаем
    if user_data.get(cid, {}).get("instruction_paid_shown"):
        return

    # Делаем кнопку неактивной СРАЗУ
    try:
        disabled_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📘 Инструкция отправляется...", callback_data="noop")]
        ])
        await call.message.edit_reply_markup(reply_markup=disabled_kb)
    except:
        pass

    # Помечаем, что кнопка уже нажата
    user_data[cid]["instruction_paid_shown"] = True

    steps = [
        "🔍 Проверяю поведение по базе кейсов... (11 000+ записей)",
        "📊 Сравниваю сигналы, взгляды, микроэмоции — всё, что считывается с фото...",
        "🧠 Строю уникальную инструкцию. Почти готово..."
    ]

    msg = await call.message.answer(steps[0])
    for step in steps[1:]:
        await asyncio.sleep(3)
        try:
            await msg.edit_text(step)
        except:
            pass
    await asyncio.sleep(1)

    payment_link = (
        f"https://yoomoney.ru/quickpay/shop-widget?"
        f"writer=seller&targets=Инструкция&default-sum=99"
        f"&button-text=14&quickpay=shop&account=410011234567890"
        f"&label={cid}&successURL=https://yourdomain.com/success"
    )

    payment_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить и получить (50 рублей)", url=payment_link)]
    ])

    await msg.edit_text("🚀 Всё готово. Жми кнопку — и инструкция будет твоей. Готов?", reply_markup=payment_kb)


    # Запоминаем, что показано
    user_data[cid]["instruction_paid_shown"] = True

    # Делаем исходную кнопку неактивной
    try:
        disabled_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📘 Инструкция уже запрошена", callback_data="noop")]
        ])
        await call.message.edit_reply_markup(reply_markup=disabled_kb)
    except:
        pass

        # Ждём 3 минуты — если не оплатил, напоминаем
    await asyncio.sleep(180)
    if not user_data.get(cid, {}).get("payment_received"):
        try:
            await bot.send_message(cid, "👀 Ты пропустил? Напоминаю, сценарий по её типажу доступен пока открыто окно 🔓", reply_markup=payment_kb)
        except:
            pass



@dp.callback_query(F.data == "agree_terms")
async def handle_agree_terms(call: CallbackQuery):
    cid = call.message.chat.id
    user_data[cid] = user_data.get(cid, {})
    user_data[cid]["agreement_accepted"] = True

    await call.message.delete()
    await call.message.answer(PROMO_TEXT)

    # запускаем напоминалку
    async def reminder():
        await asyncio.sleep(90)
        if 'photo_id' not in user_data.get(cid, {}):
            try:
                await bot.send_message(cid, "📸 Не забудь — просто пришли фото девушки...")
            except:
                pass

    asyncio.create_task(reminder())


@dp.callback_query(F.data.in_(["lust", "money", "power"]))
async def handle_analysis(call: CallbackQuery):
    cid, trait = call.message.chat.id, call.data

    analysis_steps = {
        "lust": [
            "🧠 Анализирую поведение по 11 286 кейсам...",
            "💓 Сканируем импульсы и микрореакции...",
            "🎯 Определяем паттерн флирта по базе данных...",
            "🧬 Собираем профиль привлекательности..."
        ],
        "money": [
            "🧠 Анализирую поведение по 11 286 кейсам....",
            "📊 Проверяем реакцию на статус и ресурсы...",
            "🧠 Сравниваем с типажами, склонными к выгоде...",
            "🔎 Формируем профиль интереса к материальному..."
        ],
        "power": [
            "🧠 Анализирую поведение по 11 286 кейсам...",
            "🧠 Анализируем паттерны уверенности и контроля...",
            "📊 Сравниваем с кейсами влияния и власти...",
            "🧬 Строим поведенческую модель власти/подчинения..."
        ]
    }


    steps = analysis_steps.get(trait, ["🔍 Анализ..."])


    if user_data[cid].get("is_processing"):
        await call.answer("⏳ Подожди, идёт анализ...", show_alert=False)
        return
    user_data[cid]["is_processing"] = True

    if 'results' not in user_data[cid]:
        user_data[cid]['results'] = {}

    if trait in user_data[cid]['results']:
        user_data[cid]["is_processing"] = False
        result = user_data[cid]['results'][trait]
        await call.message.edit_text(
            f"{BUTTON_TITLES[trait]}\n\n{result}",
            reply_markup=MENU_MARKUP
        )
        return

    await call.answer("Анализирую... 🔍")

    status_msg = await call.message.answer(steps[0])
    for step in steps[1:]:
        await asyncio.sleep(2)
        try:
            await status_msg.edit_text(step)
        except:
            pass
    await asyncio.sleep(2)
    try:
        await status_msg.delete()
    except:
        pass

    result = get_unique_template(cid, trait)
    user_data[cid]['results'][trait] = result
    user_data[cid]['analyzed'][trait] = True
    user_data[cid]["is_processing"] = False

    await call.message.edit_text(
        f"{BUTTON_TITLES[trait]}\n\n{result}",
        reply_markup=MENU_MARKUP
    )

    if all(user_data[cid]['analyzed'].get(t) for t in BUTTON_TITLES.keys()):
        await asyncio.sleep(7)

        final_text = (
            "💋 <b>Мы поняли, что именно её включает.</b>\n"
            "👁 Это не про банальные фразы, а про моменты, когда взгляд говорит больше слов.\n"
            "🔥 Как вести шаг за шагом — без давления, но с напряжением, которое она запомнит.\n"
            "🕯 Сценарий, где ты тот, кто знает, когда быть рядом… и когда пропасть.\n\n"
            "👇 <b>Хочешь знать, как сыграть правильно?</b> Жми — покажу, что работает в реальности."
        )

        first_heat_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📘 Получить инструкцию по шагам", callback_data="get_instruction")]
        ])

        await bot.send_message(cid, final_text, reply_markup=first_heat_kb)











from aiogram import Router, F
from aiogram.types import Message
import tempfile
import os
from deepface import DeepFace
from aiogram.types import BotCommand


# ========================== БЛОК 10: Проверка женского лица с помощью DeepFace =============

async def is_female_face(img_bytes) -> bool:
    import tempfile
    import os
    from deepface import DeepFace

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(img_bytes)
        tmp_path = tmp.name

    try:
        result = DeepFace.analyze(
            img_path=tmp_path,
            actions=["gender"],
            enforce_detection=False
        )
        gender = result[0]["dominant_gender"].lower()
        print(f"[DEBUG] DeepFace определил: {gender}")
        return gender == "woman"
    except Exception as e:
        print("❌ Ошибка DeepFace:", e)
        return False
    finally:
        os.remove(tmp_path)



    cid = message.chat.id
    photo = message.photo[-1]
    fid = photo.file_id

    # Запоминаем фото, чтобы не обрабатывать одно и то же
    user_data[cid] = {'photo_id': fid}

    photo_file = await message.bot.get_file(fid)
    file_path = photo_file.file_path
    img_bytes = await message.bot.download_file(file_path)
    img_bytes = img_bytes.read()

    if not await is_female_face(img_bytes):
        await message.answer("❌ Я работаю только с женскими фото. Попробуй другое изображение.")
        return

    await message.answer("✅ Девушка определена. Запускаю анализ...")
    # Далее твоя логика анализа




ADMIN_ID = 5236431337  # твой Telegram ID

# ========================== БЛОК 11: Команда /stats для администратора ======================

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    from stats import get_global_stats, get_all_user_stats

    data = get_global_stats()
    text = (
        f"📊 <b>Статистика бота:</b>\n\n"
        f"👥 Всего пользователей: {data['total_users']}\n"
        f"📸 Отправили фото: {data['photo_users']}\n"
        f"💳 Нажали оплату: {data['paid_users']}\n"
        f"⏱ Среднее время в боте: {data['avg_minutes']} мин\n"
        f"🕓 Активны сегодня: {data['active_today']} чел\n\n"
        f"<b>🧾 Пользователи:</b>\n{get_all_user_stats()}"
    )

    await message.answer(text)



# ========================== БЛОК 12: Ответ на любое текстовое сообщение =====================

@dp.message(F.text)
async def any_text(message: Message):
    cid = message.chat.id

    if not user_data.get(cid, {}).get("agreement_accepted"):
        await message.answer("⚠️ Чтобы продолжить, нажмите кнопку «✅ Я согласен» в пользовательском соглашении выше.")
        return

    await message.answer("📸 Загрузите фото девушки, и я сделаю AI-анализ 😉")


# ========================== БЛОК 13: Основной запуск бота ===================================

from aiohttp import web
import threading

# ========================== БЛОК 13: Основной запуск бота ===================================

from aiohttp import web

async def handle(request):
    return web.Response(text="Bot is running")

async def main():
    print("🚀 Бот запускается...")

    # Задаём сервер для Render — открываем порт
    app = web.Application()
    app.router.add_get("/", handle)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, port=10000)
    await site.start()

    # Запускаем Telegram-бота
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.delete_my_commands()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())



    from aiohttp import web

    # ========================== БЛОК 14: Обработка успешной оплаты ==============================

async def on_payment_success(request):
    data = await request.post()
    cid = data.get("label")

    if cid:
        try:
            cid = int(cid)

            # Отправка инструкции пользователю
            await bot.send_message(cid, "✅ Оплата прошла!\n\n📘 Вот твоя инструкция:\n\n"
                "1. Оцени её поведение, а не слова.\n"
                "2. Дай почувствовать твою уверенность.\n"
                "3. Используй моменты, когда она сбита с толку — это шанс проявиться.\n"
                "4. Остальное расскажем позже 😉")

            # Отправка дополнительного гайда413879413879
            await bot.send_message(cid, "📘 <b>Гайд по шагам:</b>\n\n"
                "1️⃣ Сначала зацепи внимание — фразой или взглядом.\n"
                "2️⃣ Улови её реакцию: если приостановилась — это вход.\n"
                "3️⃣ Сделай шаг вперёд, но не дави. Покажи уверенность.\n"
                "4️⃣ Сохраняй загадку: не выкладывай всё сразу.\n"
                "5️⃣ Создай микродистанцию и проявись на контрасте.\n\n"
                "✨ Это только начало. Главное — быть тем, кто не боится игры.")

            # Уведомление админа
            await bot.send_message(ADMIN_ID, f"📥 <b>Новая оплата</b> от <code>{cid}</code>")

        except Exception as e:
            print("Ошибка при отправке инструкции:", e)

    return web.Response(text="OK")
