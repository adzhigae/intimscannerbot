import logging
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor

API_TOKEN = '7588897136:AAE9zDVps4AW18O8C0ASThknPIlpFl28mUw'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start_handler(message: Message):
    await message.answer("👁 Добро пожаловать в ИнтимСканер!\n\nЗагрузи фото девушки, и я покажу тебе, что она скрывает...")

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def photo_handler(message: Message):
    await message.reply("🧠 Анализирую изображение...")
    await message.reply(generate_fake_report())

def generate_fake_report():
    fantasies = [
        "Быть пойманной в офисе", "Играть роль строгой училки", 
        "Скрытый интерес к подчинению", "Игра в доминирование"
    ]
    temperaments = ["страстная", "игривая", "загадочная", "интеллектуальная"]
    fets = ["грубые слова", "душ", "руки на талии", "запах кожи"]

    return (
        f"🔍 AI-Профиль:\n"
        f"Развратность: {random.randint(60, 99)}%\n"
        f"Темперамент: {random.choice(temperaments)}\n"
        f"Тайная фантазия: {random.choice(fantasies)}\n"
        f"Фетиш: {random.choice(fets)}\n"
        f"❤️ Совместимость с тобой: {random.randint(50, 95)}%\n"
        f"💡 Совет: подойди уверенно, но с юмором. Она это оценит 😉"
    )

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
