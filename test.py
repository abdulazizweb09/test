import os
import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto
import time
from datetime import datetime

# ==================== SOZLAMALAR ====================
API_ID = 33395092  # O'zingizning API ID'ingizni yozing
API_HASH = '9cf48140484c284e42c406755dbdfd84'  # O'zingizning API HASH'ingizni yozing
SESSION_NAME = 'video_downloader'

# Vaqtinchalik fayllar saqlanadigan papka
TEMP_DIR = 'downloads'
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# ==================== KLIENTNI YARATISH ====================
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)


# ==================== YORDAMCHI FUNKSIYALAR ====================
def get_source_info(message):
    """Xabar manbasi haqida ma'lumot qaytaradi"""
    if message.chat:
        if hasattr(message.chat, 'title') and message.chat.title:
            return f"📱 {message.chat.title}"
        elif hasattr(message.chat, 'first_name') and message.chat.first_name:
            name = message.chat.first_name
            if hasattr(message.chat, 'last_name') and message.chat.last_name:
                name += f" {message.chat.last_name}"
            username = f" (@{message.chat.username})" if message.chat.username else ""
            return f"👤 {name}{username}"
    return "📱 Noma'lum manba"


def get_media_type(message):
    """Media turini aniqlaydi"""
    if message.photo:
        return "📷 Rasm"
    elif message.video:
        return "🎥 Video"
    elif message.audio:
        return "🎵 Audio"
    elif message.voice:
        return "🎤 Ovozli xabar"
    elif message.document:
        # Dokument turini aniqlash
        for attr in message.document.attributes:
            if hasattr(attr, 'video') and attr.video:
                return "🎥 Video (dokument)"
            elif hasattr(attr, 'audio') and attr.audio:
                return "🎵 Audio (dokument)"
        return "📄 Dokument"
    elif message.sticker:
        return "😀 Stiker"
    elif message.video_note:
        return "📹 Video xabar"
    return "📎 Media"


def create_caption(message, source_info, media_type):
    """Media uchun sarlavha (caption) yaratadi"""
    caption_parts = []

    # Asl xabardagi matn
    if message.text and message.text.strip():
        caption_parts.append(message.text.strip())
        caption_parts.append("")

    # Manba ma'lumoti
    caption_parts.append(source_info)

    # Media turi
    caption_parts.append(f"📎 Tur: {media_type}")

    # Vaqt
    msg_date = message.date.strftime("%d.%m.%Y %H:%M")
    caption_parts.append(f"📅 Sana: {msg_date}")

    return "\n".join(caption_parts)


# ==================== ASOSIY FUNKSIYA ====================
async def download_and_save_to_saved(message):
    """
    Berilgan xabardagi mediani yuklab oladi va
    "Saved Messages"ga tashlaydi
    """
    try:
        # Media mavjudligini tekshirish
        if not message.media:
            print("Xabarda media yo'q")
            return False

        # Manba va media turi haqida ma'lumot
        source_info = get_source_info(message)
        media_type = get_media_type(message)
        print(f"\n➡️ Yuklanmoqda: {media_type}")
        print(f"   Manba: {source_info}")

        # Faylni yuklab olish
        filename = None
        if message.photo:
            filename = await message.download_media(file=TEMP_DIR)
        elif message.video or message.audio or message.voice or message.document or message.sticker or message.video_note:
            filename = await message.download_media(file=TEMP_DIR)
        else:
            print("❌ Qo'llab-quvvatlanmaydigan media turi")
            return False

        if not filename or not os.path.exists(filename):
            print("❌ Yuklab olish muvaffaqiyatsiz")
            return False

        print(f"✅ Yuklab olindi: {os.path.basename(filename)}")

        # Sarlavha tayyorlash
        caption = create_caption(message, source_info, media_type)

        # "Saved Messages"ga yuborish
        saved_messages = await client.get_me()
        saved_messages = await client.get_input_entity('me')

        # Media turiga qarab yuborish
        if message.photo:
            await client.send_file(saved_messages, filename, caption=caption)
        elif message.video:
            await client.send_file(saved_messages, filename, caption=caption)
        elif message.audio:
            await client.send_file(saved_messages, filename, caption=caption)
        elif message.voice:
            await client.send_file(saved_messages, filename, caption=caption)
        elif message.video_note:
            await client.send_file(saved_messages, filename, caption=caption)
        elif message.sticker:
            await client.send_file(saved_messages, filename)
        else:
            await client.send_file(saved_messages, filename, caption=caption)

        print(f"✅ Saved Messages'ga yuborildi")

        # Vaqtinchalik faylni o'chirish
        os.remove(filename)
        print(f"🧹 Vaqtinchalik fayl o'chirildi")

        return True

    except Exception as e:
        print(f"❌ Xatolik: {e}")
        return False


# ==================== LINK ORQALI YUKLASH ====================
async def process_link(link):
    """
    Telegram linkini qayta ishlaydi va videoni yuklab,
    Saved Messages'ga tashlaydi
    """
    try:
        # Linkni tahlil qilish
        if not link.startswith('https://t.me/'):
            print("❌ Noto'g'ri Telegram linki")
            return

        print(f"\n🔍 Link qayta ishlanmoqda: {link}")

        # Linkdan xabarni olish
        message = await client.get_messages(link, limit=1)

        if not message or len(message) == 0:
            print("❌ Xabar topilmadi")
            return

        message = message[0]

        # Yuklab olish va saqlash
        await download_and_save_to_saved(message)

    except Exception as e:
        print(f"❌ Xatolik: {e}")


# ==================== KOMANDA UCHUN EVENT ====================
@client.on(events.NewMessage(pattern=r'^!'))
async def command_handler(event):
    """! komandasi bilan ishlash"""
    command_text = event.message.text.strip()

    # Link bilan ! komandasi: "! https://t.me/c/2184469901/1141"
    if command_text.startswith('! ') and len(command_text) > 2:
        link = command_text[2:].strip()
        await process_link(link)

    # Javoban ! komandasi
    elif command_text == '!' and event.is_reply:
        reply_msg = await event.message.get_reply_message()
        await download_and_save_to_saved(reply_msg)


# ==================== ASOSIY FUNKSIYA ====================
async def main():
    """Dasturni ishga tushirish"""
    print("=" * 50)
    print("VIDEO YUKLAB SAVED MESSAGES'GA JO'NATUVCHI USERBOT")
    print("=" * 50)
    print("\n🚀 Ishga tushmoqda...")

    await client.start()
    print("✅ Userbot ishga tushdi!")
    print("\n📌 Qanday ishlatish:")
    print("   1. Link bilan:  ! https://t.me/c/2184469901/1141")
    print("   2. Javoban:     Xabarga javoban '!' yozing")
    print("\n⏸️ To'xtatish uchun: Ctrl+C")
    print("=" * 50)

    await client.run_until_disconnected()


# ==================== ISHGA TUSHIRISH ====================
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Userbot to'xtatildi")
    except Exception as e:
        print(f"\n❌ Kutilmagan xatolik: {e}")
