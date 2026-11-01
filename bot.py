import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
import yt_dlp

TOKEN = "9138101810:AAE4wNX2iGT-2WbEwIb_fbzDwfThvLIcBXE"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- РАБОТА С БАЗОЙ ДАННЫХ (ПИТОМЕЦ) ---
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pets (
            user_id INTEGER PRIMARY KEY,
            pet_name TEXT DEFAULT 'Пиксель',
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_or_create_pet(user_id: int):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT pet_name, level, xp FROM pets WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row:
        cursor.execute("INSERT INTO pets (user_id, pet_name, level, xp) VALUES (?, 'Пиксель', 1, 0)", (user_id,))
        conn.commit()
        row = ('Пиксель', 1, 0)
    
    conn.close()
    return {"name": row[0], "level": row[1], "xp": row[2]}

def add_xp(user_id: int, amount: int = 20):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    pet = get_or_create_pet(user_id)
    
    new_xp = pet["xp"] + amount
    new_level = pet["level"]
    
    # Каждые 100 XP питомец растет на уровень
    if new_xp >= 100:
        new_level += 1
        new_xp -= 100
        
    cursor.execute("UPDATE pets SET xp = ?, level = ? WHERE user_id = ?", (new_xp, new_level, user_id))
    conn.commit()
    conn.close()
    return new_level > pet["level"] # Вернет True, если питомец повысил уровень!


# --- КОМАНДЫ БОТА ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    get_or_create_pet(message.from_user.id)
    await message.answer(
        "Привет! 🎬 Я Clipix — бот для скачивания видео без водяных знаков.\n\n"
        "🐱 У тебя появился свой кибер-питомец! Скачивай видео, чтобы растить его.\n"
        "Команды:\n"
        "🐾 /pet — посмотреть на своего питомца"
    )

@dp.message(Command("pet"))
async def cmd_pet(message: types.Message):
    pet = get_or_create_pet(message.from_user.id)
    await message.answer(
        f"🐾 Твой питомец: **{pet['name']}**\n"
        f"⭐ Уровень: `{pet['level']}`\n"
        f"📈 Опыт (XP): `{pet['xp']}/100`\n\n"
        f"💡 *Скачивай видео, чтобы питомец набирался сил и рос!*"
    )


# --- СКАЧИВАНИЕ ВИДЕО + ПРОКАЧКА ---
@dp.message(F.text.startswith("http"))
async def download_video(message: types.Message):
    url = message.text.strip()
    status_msg = await message.answer("⏳ Скачиваю видео, подожди пару секунд...")
    
    output_filename = f"video_{message.from_user.id}.mp4"

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_filename,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))

        if os.path.exists(output_filename):
            video_file = types.FSInputFile(output_filename)
            
            # Начисляем опыт питомцу за успешное скачивание!
            leveled_up = add_xp(message.from_user.id, amount=30)
            
            caption = "Вот твое видео! 🚀\n🐱 *Питомец получил +30 опыта!*"
            if leveled_up:
                caption += "\n🎉 **Поздравляем! Твой питомец повысил уровень!**"

            await message.answer_video(video=video_file, caption=caption)
            os.remove(output_filename)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Не удалось сохранить видео. Попробуй другую ссылку.")

    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка при скачивании: {str(e)[:100]}")
        if os.path.exists(output_filename):
            os.remove(output_filename)


async def main():
    init_db()
    print("Бот с питомцем запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
