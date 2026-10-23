# -*- coding: utf-8 -*-
import asyncio
import os
import aiohttp
from threading import Thread
from flask import Flask
from rubpy import Client
from rubpy.types import Update

# ==========================================
# ⚙️ تنظیمات اصلی
# ==========================================
SESSION_NAME = "my_userbot_session"
MAJID_API_TOKEN = "*9mnlrt7c0r4y55h:i16MIfO7j8UkrfuReXob*"

# ⚠️ این دو مقدار را بعدا باید پیدا کنی و اینجا بذاری
GROUP_GUID = "b0..."  
CALL_GUID = "c0..."   

# ==========================================
# 🌐 وب‌سرور کوچک برای زنده نگه داشتن ربات در Render
# ==========================================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

# ==========================================
# 🎵 کلاس مدیریت پخش
# ==========================================
class MusicPlayer:
    def __init__(self, client: Client):
        self.client = client
        self.is_playing = False
        self.current_file = None

    async def play(self, file_path: str):
        if not os.path.exists(file_path):
            return "❌ فایل صوتی پیدا نشد."
        try:
            await self.client.voice_chat_player(CALL_GUID, file_path)
            self.is_playing = True
            self.current_file = file_path
            return f"🎶 در حال پخش: {os.path.basename(file_path)}"
        except Exception as e:
            return f"❌ خطا در پخش: {e}"

    async def stop(self):
        if not self.is_playing:
            return "⚠️ چیزی در حال پخش نیست."
        if hasattr(self.client, 'stop_voice_chat_player'):
            await self.client.stop_voice_chat_player(CALL_GUID)
        self.is_playing = False
        return "⏹️ پخش متوقف شد."

# ==========================================
# 🤖 راه‌اندازی کلاینت
# ==========================================
app = Client(SESSION_NAME)
player = MusicPlayer(app)

@app.on_message_updates()
async def handle_messages(update: Update):
    msg = update.new_message
    if not msg: return
    
    # دستور مخفی برای پیدا کردن GROUP_GUID
    if msg.text == "راهنما_شناسه":
        print("\n" + "="*40)
        print(f"✅ شناسه گروه (GROUP_GUID): {msg.object_guid}")
        print("="*40 + "\n")
        await msg.reply("شناسه گروه در لاگ‌های رندر چاپ شد ✅")

    if msg.object_guid == GROUP_GUID and msg.text:
        text = msg.text.strip()

        if text.startswith("پخش "):
            song_name = text.replace("پخش ", "", 1)
            await msg.reply(f"🔍 در حال جستجوی «{song_name}»...")
            
            try:
                search_url = f"https://api.majidapi.ir/music/radiojavan?action=search&s={song_name}&token={MAJID_API_TOKEN}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(search_url) as resp:
                        data = await resp.json()
                        
                        if isinstance(data, dict) and "error" in data:
                            await msg.reply(f"❌ خطای API: {data['error']}")
                            return

                        songs = data if isinstance(data, list) else data.get('data', [])
                        if not songs:
                            await msg.reply("❌ آهنگی پیدا نشد.")
                            return

                        first_song = songs[0]
                        song_url = first_song.get('link') or first_song.get('download_url')
                        
                        if not song_url:
                            await msg.reply("❌ لینک دانلود یافت نشد.")
                            return

                        file_path = f"download_{song_name}.mp3"
                        await msg.reply("⬇️ در حال دانلود...")
                        async with session.get(song_url) as audio_resp:
                            if audio_resp.status == 200:
                                with open(file_path, 'wb') as f:
                                    f.write(await audio_resp.read())
                            else:
                                await msg.reply("❌ دانلود با خطا مواجه شد.")
                                return

                result = await player.play(file_path)
                await msg.reply(result)

            except Exception as e:
                await msg.reply(f"❌ خطای غیرمنتظره: {e}")

        elif text == "توقف":
            result = await player.stop()
            await msg.reply(result)

@app.on_update()
async def catch_call_updates(update: Update):
    upd_type = str(getattr(update, 'type', ''))
    if 'voice' in upd_type.lower() or 'call' in upd_type.lower():
        print("\n📞 آپدیت کال:")
        print(update)
        print("👆 دنبال کد c0... بگرد\n")

# ==========================================
# 🚀 اجرا
# ==========================================
if __name__ == "__main__":
    # اجرای وب‌سرور در یک ترد جداگانه
    Thread(target=run_web).start()
    print("✅ وب‌سرور و ربات فعال شدند...")
    app.run()