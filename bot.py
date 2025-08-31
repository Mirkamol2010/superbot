import json
import os
from aiogram import Bot, Dispatcher, executor, types

# Token va admin ID ni ENV orqali olish
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# JSON fayl yo‘llari
USERS_FILE = "data/users.json"
QUESTIONS_FILE = "data/questions.json"
SETTINGS_FILE = "data/settings.json"


def load_json(filename):
    if not os.path.exists(filename):
        if "users" in filename:
            data = {}
        elif "questions" in filename:
            data = []
        elif "settings" in filename:
            data = {"reward": 1000, "channels": []}
        else:
            data = {}
        save_json(filename, data)
        return data
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    users = load_json(USERS_FILE)
    if str(message.from_user.id) not in users:
        users[str(message.from_user.id)] = {"balance": 0, "username": message.from_user.username}
        save_json(USERS_FILE, users)
    await message.answer("👋 Salom! Bu mukammal bot.\nSavollarga javob bering va pul yuting!")


@dp.message_handler(commands=["help"])
async def help_cmd(message: types.Message):
    await message.answer("/start - Botni ishga tushirish\n/balance - Balansni ko‘rish\n/quiz - Testni boshlash")


@dp.message_handler(commands=["balance"])
async def balance_cmd(message: types.Message):
    users = load_json(USERS_FILE)
    bal = users.get(str(message.from_user.id), {}).get("balance", 0)
    await message.answer(f"💰 Sizning balansingiz: {bal} so‘m")


@dp.message_handler(commands=["quiz"])
async def quiz_cmd(message: types.Message):
    questions = load_json(QUESTIONS_FILE)
    if not questions:
        await message.answer("❌ Hozircha savollar yo‘q.")
        return
    q = questions[0]
    keyboard = types.InlineKeyboardMarkup()
    for i, ans in enumerate(q["answers"]):
        keyboard.add(types.InlineKeyboardButton(ans, callback_data=f"ans_{i}_{q['correct']}_{q['id']}"))
    await message.answer(q["question"], reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith("ans_"))
async def answer_handler(callback: types.CallbackQuery):
    _, chosen, correct, qid = callback.data.split("_")
    users = load_json(USERS_FILE)
    settings = load_json(SETTINGS_FILE)
    if chosen == correct:
        users[str(callback.from_user.id)]["balance"] += settings["reward"]
        save_json(USERS_FILE, users)
        await callback.message.answer(f"✅ To‘g‘ri! Siz {settings['reward']} so‘m yutdingiz.")
    else:
        await callback.message.answer("❌ Noto‘g‘ri javob.")
    await callback.answer()


# Admin komandalar
@dp.message_handler(commands=["addq"])
async def add_question(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Siz admin emassiz.")
    try:
        parts = message.text.split("|")
        q_text = parts[1]
        answers = parts[2:6]
        correct = int(parts[6])
        qid = len(load_json(QUESTIONS_FILE)) + 1
        questions = load_json(QUESTIONS_FILE)
        questions.append({"id": qid, "question": q_text, "answers": answers, "correct": correct})
        save_json(QUESTIONS_FILE, questions)
        await message.answer("✅ Savol qo‘shildi.")
    except:
        await message.answer("❌ Format xato. Namuna:\n/addq |Savol|javob1|javob2|javob3|javob4|0")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

