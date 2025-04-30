import os
import openai
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, executor

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("MODEL", "gpt-3.5-turbo")

if not BOT_TOKEN or not OPENROUTER_API_KEY:
    raise ValueError("BOT_TOKEN или OPENROUTER_API_KEY отсутствует!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

openai.api_key = OPENROUTER_API_KEY
openai.api_base = "https://openrouter.ai/api/v1"

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("👋 Привет! Отправь мне любой текст, и я дам нейросетевой анализ 😉")

@dp.message_handler()
async def analyze_message(message: types.Message):
    await message.chat.do("typing")
    try:
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Отвечай игриво, как психолог-флиртолог. Без грубостей. Анализируй с юмором."},
                {"role": "user", "content": message.text}
            ]
        )
        reply = response['choices'][0]['message']['content']
        await message.reply(reply)
    except Exception as e:
        await message.reply("⚠️ Ошибка анализа. Проверь ключ OpenRouter.\n" + str(e))

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
