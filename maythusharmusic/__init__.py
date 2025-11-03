# Powered By Team maythusharmusic
from maythusharmusic.core.bot import Cailin
from maythusharmusic.core.dir import dirr
from maythusharmusic.core.git import git
from maythusharmusic.core.userbot import Userbot
from maythusharmusic.misc import dbb, heroku

from .logging import LOGGER

dirr()
git()
dbb()
heroku()

app = Cailin()
userbot = Userbot()


from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()
