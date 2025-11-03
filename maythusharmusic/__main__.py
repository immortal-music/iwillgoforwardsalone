# Powered By Team maythusharmusic

import asyncio
import importlib

from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from maythusharmusic import LOGGER, app, userbot
from maythusharmusic.core.call import Cailin
from maythusharmusic.misc import sudo
from maythusharmusic.plugins import ALL_MODULES
from maythusharmusic.utils.database import get_banned_users, get_gbanned
from maythusharmusic.utils.crash_reporter import setup_global_exception_handler  # ✅ Import crash handler
from config import BANNED_USERS

async def init():
    # ✅ Enable global crash handler
    setup_global_exception_handler()

  
    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).error("Assistant client variables not defined, exiting...")
        exit()
    await sudo()
    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except:
        pass
    await app.start()
    for all_module in ALL_MODULES:
        importlib.import_module("maythusharmusic.plugins" + all_module)
    LOGGER("maythusharmusic.plugins").info("Successfully Imported Modules...")
    await userbot.start()
    await Cailin.start()
    try:
        await Cailin.stream_call("https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4")
    except NoActiveGroupCall:
        LOGGER("maythusharmusic").error(
            "Please turn on the videochat of your log group\channel.\n\nStopping Bot..."
        )
        exit()
    except:
        pass
    await Cailin.decorators()
    LOGGER("maythusharmusic").info(
        "maythusharmusic Music Bot started successfully"
    )
    await idle()
    await app.stop()
    await userbot.stop()
    LOGGER("maythusharmusic").info("Stopping maythusharmusic Music Bot...")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())
