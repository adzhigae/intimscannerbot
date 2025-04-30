import logging
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = "7588897136:AAE9zDVps4AW18O8C0ASThknPIlpFl28mUw"
OPENROUTER_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class Form(StatesGroup):
    mode = State()
    photo1 = State()
    photo2 = State()

start_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("🧠 Узнать всё про девушку", callback_data="mode_girl"),
    InlineKeyboardButton("💘 Шанс на сближение (2 фото)", callback_data="mode_match")
)

girl_options_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("✨ Предпочтения", callback_data="girl_pref"),
    InlineKeyboardButton("🛏️ В близости", callback_data="girl_bed"),
    InlineKeyboardButton("🧬 Внешность", callback_data="girl_look")
)

match_options_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("💞 Совместимость", callback_data="match_score"),
    InlineKeyboardButton("🧭 Как действовать", callback_data="match_tip"),
    InlineKeyboardButton("🧠 Что её цепляет", callback_data="match_trigger")
)

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать в ИнтимСканер!

"
        "Этот бот генерирует 🔥 нейроанализ по фото. Всё конфиденциально, фото не сохраняются.

"
        "Выбери режим:", reply_markup=start_kb)

@dp.callback_query_handler(lambda c: c.data.startswith("mode_"))
async def choose_mode(callback_query: types.CallbackQuery, state: FSMContext):
    mode = callback_query.data.split("_")[1]
    await state.update_data(mode=mode)
    await bot.send_message(callback_query.from_user.id,
        "📸 Загрузите фото девушки:" if mode == "girl" else "📸 Загрузите фото девушки (1/2):")
    await Form.photo1.set()

@dp.message_handler(content_types=types.ContentType.PHOTO, state=Form.photo1)
async def get_photo1(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.update_data(photo1=message.photo[-1].file_id)

    if data.get("mode") == "match":
        await message.answer("📸 Загрузите ваше фото (2/2):")
        await Form.photo2.set()
    else:
        await message.answer("Выберите, что узнать:", reply_markup=girl_options_kb)

@dp.message_handler(content_types=types.ContentType.PHOTO, state=Form.photo2)
async def get_photo2(message: types.Message, state: FSMContext):
    await state.update_data(photo2=message.photo[-1].file_id)
    await message.answer("Выберите, что узнать:", reply_markup=match_options_kb)

@dp.callback_query_handler(lambda c: c.data.startswith("girl_") or c.data.startswith("match_"), state="*")
async def process_analysis(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.send_message(callback_query.from_user.id, "🧠 Анализирую нейросетью...")
    topic = callback_query.data

    prompt_map = {
        "girl_pref": "Опиши сексуальные предпочтения девушки по фото. Кратко, по делу, на грани.",
        "girl_bed": "Как она ведёт себя в близости. Прямо, игриво, без пошлости.",
        "girl_look": "Что говорит её внешность о её желаниях и стиле общения.",
        "match_score": "Проанализируй совместимость по двум фото. Дай процент шанса на сближение.",
        "match_tip": "Что парню делать, чтобы сближение с ней произошло быстрее.",
        "match_trigger": "Что может её зацепить — поведение, прикосновения, настрой."
    }

    response = await generate_ai_response(prompt_map.get(topic, "Дай провокационный психологический разбор по фото."))

    await bot.send_message(callback_query.from_user.id, response)

async def generate_ai_response(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "Ты психолог-нейроаналитик, который делает сексуально-психологический разбор по фото. Пиши кратко, возбуждающе, но не нарушай цензуру. Без слов 'секс', 'порно', 'ебля'. Стиль — уверенный, игривый, нейросетевой."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_URL, headers=headers, json=payload) as response:
                data = await response.json()
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Ошибка нейросети: {e}"

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)