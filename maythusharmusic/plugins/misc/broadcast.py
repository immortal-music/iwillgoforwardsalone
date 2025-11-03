# Powered By Team maythusharmusic

import time
import logging
import asyncio

from pyrogram import filters
from pyrogram.enums import ChatMembersFilter
from pyrogram.errors import FloodWait, RPCError
from pyrogram.types import Message

from maythusharmusic import app
from maythusharmusic.misc import SUDOERS
from maythusharmusic.utils.database import (
    get_active_chats,
    get_authuser_names,
    get_client,
    get_served_chats,
    get_served_users,
)
from maythusharmusic.utils.decorators.language import language
from maythusharmusic.utils.formatters import alpha_to_int
from config import adminlist

# Global broadcast status
BROADCAST_STATUS = {
    "active": False,
    "sent": 0,
    "failed": 0,
    "total": 0,
    "start_time": 0,
    "users": 0,
    "chats": 0,
    "mode": "",
    "sent_users": 0,
    "sent_chats": 0,
}



@app.on_message(filters.command("broadcast") & SUDOERS)
async def broadcast_command(client, message: Message):
    global BROADCAST_STATUS

    command = message.text.lower()
    mode = "forward" if "-forward" in command else "copy"

    # Determine recipients
    if "-all" in command:
        users = await get_served_users()
        chats = await get_served_chats()
        target_users = [u["user_id"] for u in users]
        target_chats = [c["chat_id"] for c in chats]
    elif "-users" in command:
        users = await get_served_users()
        target_users = [u["user_id"] for u in users]
        target_chats = []
    elif "-chats" in command:
        chats = await get_served_chats()
        target_chats = [c["chat_id"] for c in chats]
        target_users = []
    else:
        return await message.reply_text("❗ Usage:\n-broadcast -all/-users/-chats [-forward]")

    if not target_users and not target_chats:
        return await message.reply_text("⚠ No recipients found.")

    # Get content
    if message.reply_to_message:
        content = message.reply_to_message
    else:
        text = message.text
        for kw in ["/broadcast", "-forward", "-all", "-users", "-chats"]:
            text = text.replace(kw, "")
        text = text.strip()
        if not text:
            return await message.reply_text("📝 Provide a message or reply to one.")
        content = text

    # Initialize status
    targets = target_users + target_chats
    total = len(targets)
    BROADCAST_STATUS.update({
        "active": True,
        "sent": 0,
        "failed": 0,
        "total": total,
        "start_time": time.time(),
        "users": len(target_users),
        "chats": len(target_chats),
        "mode": mode,
    })

    status_msg = await message.reply_text("📡 Broadcasting started...")

    async def deliver(chat_id):
        try:
            if isinstance(content, str):
                await app.send_message(chat_id, content)
            elif mode == "forward":
                await app.forward_messages(chat_id, message.chat.id, [content.id])
            else:
                await content.copy(chat_id)
            BROADCAST_STATUS["sent"] += 1
            if chat_id in target_users:
                BROADCAST_STATUS["sent_users"] += 1
            else:
                BROADCAST_STATUS["sent_chats"] += 1
        except FloodWait as e:
            await asyncio.sleep(min(e.value, 60))  # Limit max sleep
            return await deliver(chat_id)  # Retry after wait
        except RPCError:
            BROADCAST_STATUS["failed"] += 1
        except Exception as e:
            BROADCAST_STATUS["failed"] += 1
            logging.exception(f"Unhandled error for chat {chat_id}: {e}")

    # Broadcast in batches to avoid memory/flood issues
    BATCH_SIZE = 100
    for i in range(0, total, BATCH_SIZE):
        batch = targets[i:i + BATCH_SIZE]
        tasks = [deliver(chat_id) for chat_id in batch]
        await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(1.5)  # Delay between batches

        # Update status message (optionally)
        percent = round((BROADCAST_STATUS["sent"] + BROADCAST_STATUS["failed"]) / total * 100, 2)
        await status_msg.edit_text(
            f"📣 <b>Broadcast In Progress</b>\n"
            f"✅ Sent: <code>{BROADCAST_STATUS['sent']}</code>\n"
            f"❌ Failed: <code>{BROADCAST_STATUS['failed']}</code>\n"
            f"📦 Total Targets: <code>{BROADCAST_STATUS['total']}</code>\n"
            f"    ├ Users: <code>{BROADCAST_STATUS['users']}</code>\n"
            f"    └ Chats: <code>{BROADCAST_STATUS['chats']}</code>\n"
            f"🔃 Progress: <code>{percent}%</code>"
        )

    BROADCAST_STATUS["active"] = False
    elapsed = round(time.time() - BROADCAST_STATUS["start_time"])
    await status_msg.edit_text(
        f"✅ <b>Broadcast Complete!</b>\n\n"
        f"🔘 Mode: <code>{BROADCAST_STATUS['mode']}</code>\n"
        f"📦 Total Targets: <code>{BROADCAST_STATUS['total']}</code>\n"
        f"📬 Delivered: <code>{BROADCAST_STATUS['sent']}</code>\n"
        f"    ├ Users: <code>{BROADCAST_STATUS['sent_users']}</code>\n"
        f"    └ Chats: <code>{BROADCAST_STATUS['sent_chats']}</code>\n"
        f"❌ Failed: <code>{BROADCAST_STATUS['failed']}</code>\n"
        f"⏰ Time Taken: <code>{elapsed}s</code>"
    )


@app.on_message(filters.command("status") & SUDOERS)
async def broadcast_status(client, message):
    if not BROADCAST_STATUS["active"]:
        return await message.reply_text("📡 No active broadcast.")
    elapsed = round(time.time() - BROADCAST_STATUS["start_time"])
    sent = BROADCAST_STATUS["sent"]
    failed = BROADCAST_STATUS["failed"]
    total = BROADCAST_STATUS["total"]
    percent = round((sent + failed) / total * 100, 2)

    eta = (elapsed / max((sent + failed), 1)) * (total - (sent + failed))
    eta_fmt = f"{int(eta // 60)}m {int(eta % 60)}s"

    bar = f"[{'█' * int(percent // 5)}{'░' * (20 - int(percent // 5))}]"

    await message.reply_text(
        f"📊 <b>Live Broadcast Status</b>\n\n"
        f"{bar} <code>{percent}%</code>\n"
        f"✅ Sent: <code>{sent}</code>\n"
        f"❌ Failed: <code>{failed}</code>\n"
        f"📦 Total: <code>{total}</code>\n"
        f"⏱ ETA: <code>{eta_fmt}</code>\n"
        f"🕒 Elapsed: <code>{elapsed}s</code>"
    )


async def auto_clean():
    while not await asyncio.sleep(10):
        try:
            served_chats = await get_active_chats()
            for chat_id in served_chats:
                if chat_id not in adminlist:
                    adminlist[chat_id] = []
                    async for user in app.get_chat_members(
                        chat_id, filter=ChatMembersFilter.ADMINISTRATORS
                    ):
                        if user.privileges.can_manage_video_chats:
                            adminlist[chat_id].append(user.user.id)
                    authusers = await get_authuser_names(chat_id)
                    for user in authusers:
                        user_id = await alpha_to_int(user)
                        adminlist[chat_id].append(user_id)
        except:
            continue


asyncio.create_task(auto_clean())
