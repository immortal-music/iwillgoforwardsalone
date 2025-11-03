import asyncio
from datetime import datetime, timedelta
import pytz

from pyrogram.enums import ChatType

import config
from maythusharmusic import app
from maythusharmusic.utils.database import get_client, is_active_chat

# Calculate seconds until next 4:35 AM
def seconds_until_435am():
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)
    target = now.replace(hour=4, minute=35, second=0, microsecond=0)
    if now >= target:
        target += timedelta(days=1)
    return (target - now).total_seconds()
    
async def auto_leave():
    if config.AUTO_LEAVING_ASSISTANT:
        print("maythusharmusic.plugins.misc.Auto_leave Task started.")
        while True:
            sleep_duration = seconds_until_435am()
            print(f"maythusharmusic.plugins.misc.Auto_leave Sleeping for {sleep_duration} seconds until 4:35 AM.")
            await asyncio.sleep(sleep_duration)

            from maythusharmusic.core.userbot import assistants

            for num in assistants:
                client = await get_client(num)
                left = 0
                try:
                    async for dialog in client.get_dialogs():
                        chat = dialog.chat
                        if chat.type in [ChatType.SUPERGROUP, ChatType.GROUP, ChatType.CHANNEL]:
                            if chat.id not in [config.LOGGER_ID, -1001686672798, -1001549206010]:
                                if left >= 20:
                                    break
                                if not await is_active_chat(chat.id):
                                    try:
                                        await client.leave_chat(chat.id)
                                        print(f"[AutoLeave] {client.me.first_name} left: {chat.title} ({chat.id})")
                                        left += 1
                                    except Exception as e:
                                        print(f"[AutoLeave Error] Could not leave {chat.title} ({chat.id}): {e}")
                except Exception as e:
                    print(f"[AutoLeave Error] Assistant {num} failed to fetch dialogs: {e}")

# Start background task
asyncio.create_task(auto_leave())
