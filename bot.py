import os
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
import yt_dlp

TOKEN = "9138101810:AAE4wNX2iGT-2WbEwIb_fbzDwfThvLIcBXE"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Привет! Отправь мне ссылку на видео (TikTok, Reels, Shorts), и я скачаю его для тебя без водяных знаков.")

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
            await message.answer_video(video=video_file, caption="Вот твое видео! 🚀")
            os.remove(output_filename)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Не удалось сохранить видео. Попробуй другую ссылку.")

    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка при скачивании: {str(e)[:100]}")
        if os.path.exists(output_filename):
            os.remove(output_filename)

async def main():
    print("Бот запущен в облаке Render!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
