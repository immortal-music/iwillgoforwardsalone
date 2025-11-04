import asyncio
import os
import re
import json
import requests
import aiohttp  # <-- 1. API အတွက် import ထည့်ပါ
from typing import Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch

from maythusharmusic.utils.database import is_on_off
from maythusharmusic.utils.formatters import time_to_seconds

import glob
import random
import logging
#import config
#from config import API_URL, API_KEY

# --- START: API Download Function ---
#API_KEY = "30DxNexGenBotsfcfad8"
#API_URL = "https://api.thequickearn.xyz"

# ✅ Configurable constants
API_KEY = "AIzaSyBEVMC-x-UDBAarphdeDtrU4bI0X6iY6iE"
API_BASE_URL = "https://www.youtube.com"

MIN_FILE_SIZE = 51200

def extract_video_id(link: str) -> str:
    patterns = [
        r'youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=)([0-9A-Za-z_-]{11})',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'youtube\.com\/(?:playlist\?list=[^&]+&v=|v\/)([0-9A-Za-z_-]{11})',
        r'youtube\.com\/(?:.*\?v=|.*\/)([0-9A-Za-z_-]{11})'
    ]

    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            return match.group(1)

    raise ValueError("Invalid YouTube link provided.")
    


def api_dl(video_id: str) -> str | None:
    api_url = f"{API_BASE_URL}/download/song/{video_id}?key={API_KEY}"
    file_path = os.path.join("downloads", f"{video_id}.mp3")

    # ✅ Check if already downloaded
    if os.path.exists(file_path):
        print(f"{file_path} already exists. Skipping download.")
        return file_path

    try:
        response = requests.get(api_url, stream=True, timeout=10)

        if response.status_code == 200:
            os.makedirs("downloads", exist_ok=True)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # ✅ Check file size
            file_size = os.path.getsize(file_path)
            if file_size < MIN_FILE_SIZE:
                print(f"Downloaded file is too small ({file_size} bytes). Removing.")
                os.remove(file_path)
                return None

            print(f"Downloaded {file_path} ({file_size} bytes)")
            return file_path

        else:
            print(f"Failed to download {video_id}. Status: {response.status_code}")
            return None

    except requests.RequestException as e:
        print(f"Download error for {video_id}: {e}")
        return None

    except OSError as e:
        print(f"File error for {video_id}: {e}")
        return None


async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0?]*[ -/]*[@-~])")

        # --- START: COOKIE HANDLING ---
        self.cookie_file_path = "cookies.txt"
        self.cookie_arg = []  # For subprocess
        self.cookie_dict = {} # For Python library
        
        if os.path.exists(self.cookie_file_path):
            logging.info(f"'{self.cookie_file_path}' file found. Using it for yt-dlp.")
            self.cookie_arg = ["--cookie", self.cookie_file_path]
            self.cookie_dict = {"cookiefile": self.cookie_file_path}
        else:
            logging.warning(f"'{self.cookie_file_path}' not found. yt-dlp will run without cookies.")
        # --- END: COOKIE HANDLING ---

    async def check_file_size(self, link):
        async def get_format_info(link):
            cmd_args = ["yt-dlp", "-J"] + self.cookie_arg + [link]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                print(f'Error:\n{stderr.decode()}')
                return None
            return json.loads(stdout.decode())

        def parse_size(formats):
            total_size = 0
            for format in formats:
                if 'filesize' in format and format['filesize']:
                    total_size += format['filesize']
            return total_size

        info = await get_format_info(link)
        if info is None:
            return None
        
        formats = info.get('formats', [])
        if not formats:
            print("No formats found.")
            return None
        
        total_size = parse_size(formats)
        return total_size

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if re.search(self.regex, link):
            return True
        else:
            return False

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset in (None,):
            return None
        return text[offset : offset + length]

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        # --- START: Fix for search result error ---
        try:
            search_results = (await results.next()).get("result", [])
            if not search_results:
                raise Exception("No search results found.")
            
            result = search_results[0]
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            if str(duration_min) == "None":
                duration_sec = 0
            else:
                duration_sec = int(time_to_seconds(duration_min))
            return title, duration_min, duration_sec, thumbnail, vidid
        except Exception as e:
            logging.error(f"Error in YouTubeAPI.details: {e}")
            return None, None, 0, None, None
        # --- END: Fix ---


    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        try:
            for result in (await results.next())["result"]:
                title = result["title"]
            return title
        except:
            return "Unsupported Title"

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        try:
            for result in (await results.next())["result"]:
                duration = result["duration"]
            return duration
        except:
            return "00:00"

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        try:
            for result in (await results.next())["result"]:
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            return thumbnail
        except:
            return None # Return None if not found

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        cmd_args = [
            "yt-dlp",
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
        ] + self.cookie_arg + [f"{link}"]
            
        proc = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            return 0, stderr.decode()

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
            
        cookie_cmd = f"--cookie {self.cookie_file_path}" if self.cookie_arg else ""
            
        playlist = await shell_cmd(
            f"yt-dlp -i {cookie_cmd} --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = playlist.split("\n")
            result = [r for r in result if r] # ရှင်းလင်းသောနည်း
        except:
            result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        try:
            for result in (await results.next())["result"]:
                title = result["title"]
                duration_min = result["duration"]
                vidid = result["id"]
                yturl = result["link"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            track_details = {
                "title": title,
                "link": yturl,
                "vidid": vidid,
                "duration_min": duration_min,
                "thumb": thumbnail,
            }
            return track_details, vidid
        except Exception as e:
            logging.error(f"Error in YouTubeAPI.track: {e}")
            return None, None

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
            
        ytdl_opts = {"quiet": True, **self.cookie_dict}
        
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    str(format["format"])
                except:
                    continue
                if not "dash" in str(format["format"]).lower():
                    try:
                        format["format"]
                        format["filesize"]
                        format["format_id"]
                        format["ext"]
                        format["format_note"]
                    except:
                        continue
                    formats_available.append(
                        {
                            "format": format["format"],
                            "filesize": format.get("filesize"), # .get() သုံးပါ
                            "format_id": format["format_id"],
                            "ext": format["ext"],
                            "format_note": format["format_note"],
                            "yturl": link,
                        }
                    )
        return formats_available, link

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link
        loop = asyncio.get_running_loop()
        
        # --- START: yt-dlp Fallback Function ---
        def audio_dl_fallback():
            # yt-dlp (cookie) ကို fallback အဖြစ်သုံးပါ
            logging.warning("API download failed or skipped, falling back to yt-dlp.")
            ydl_optssx = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                **self.cookie_dict, # COOKIE
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz
        # --- END: yt-dlp Fallback Function ---

        def video_dl():
            ydl_optssx = {
                "format": "bestvideo[height<=?720]+bestaudio/best[height<=?720]", # 720p Fix
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                **self.cookie_dict, # COOKIE
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def song_video_dl():
            formats = f"{format_id}+140"
            fpath = f"downloads/{title}"
            ydl_optssx = {
                "format": formats,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4",
                **self.cookie_dict, # COOKIE
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        def song_audio_dl():
            fpath = f"downloads/{title}.%(ext)s"
            ydl_optssx = {
                "format": format_id,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "320",
                    }
                ],
                **self.cookie_dict, # COOKIE
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        if songvideo:
            await loop.run_in_executor(None, song_video_dl)
            fpath = f"downloads/{title}.mp4"
            return fpath
        elif songaudio:
            await loop.run_in_executor(None, song_audio_dl)
            fpath = f"downloads/{title}.mp3"
            return fpath
        elif video:
            # --- START: Video Fast Mode (Always Stream) ---
            if False: # if await is_on_off(0.1): # Setting ကို False လုပ်ပြီး အမြဲ stream ခိုင်း
                direct = True
                downloaded_file = await loop.run_in_executor(None, video_dl)
            else:
                # Video Stream (Fast Mode)
                cmd_args = [
                    "yt-dlp",
                    "-g",
                    "-f",
                    "best[height<=?720][width<=?1280]",
                ] + self.cookie_arg + [f"{link}"]
                
                proc = await asyncio.create_subprocess_exec(
                    *cmd_args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                if stdout:
                    downloaded_file = stdout.decode().split("\n")[0]
                    direct = False
                else:
                    # Video Stream မရရင် Fallback
                    file_size = await self.check_file_size(link) 
                    if not file_size:
                        print("None file Size")
                        return None, None 
                    total_size_mb = file_size / (1024 * 1024)
                    if total_size_mb > 250: 
                        print(f"File size {total_size_mb:.2f} MB exceeds 250MB limit.")
                        return None, None 
                    direct = True
                    downloaded_file = await loop.run_in_executor(None, video_dl)
            # --- END: Video Fast Mode ---
        else:
            # --- START: Audio Download/Stream Logic (API-First) ---
            if await is_on_off(1): # is_on_off(1) ကို ပြန်ပြင်ထား
                # Mode 1: Download (slow)
                direct = True
                
                # --- START: API-First Logic ---
                logging.info(f"Attempting API download for: {link}")
                try:
                    video_id = extract_video_id(link)
                except ValueError:
                    video_id = None
                    
                if video_id:
                    downloaded_file = await loop.run_in_executor(None, api_dl, video_id)
                else:
                    downloaded_file = None
                    
                if downloaded_file is None:
                    # 2. API မအောင်မြင်မှ yt-dlp ကိုခေါ်
                    downloaded_file = await loop.run_in_executor(None, audio_dl_fallback)
                # --- END: API-First Logic ---
                
            else:
                # Mode 2: Stream (fast) - yt-dlp only
                direct = False
                cmd_args = [
                    "yt-dlp",
                    "-g",
                    "-f",
                    "bestaudio[ext=m4a]/bestaudio/best",
                ] + self.cookie_arg + [f"{link}"]
                
                proc = await asyncio.create_subprocess_exec(
                    *cmd_args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                if stdout:
                    downloaded_file = stdout.decode().split("\n")[0]
                else:
                    # Stream မရရင် Download mode (API-First) ကို ပြန်ခေါ်
                    logging.warning(f"Streaming failed for {link}, falling back to download...")
                    direct = True
                    # --- START: API-First Logic (Fallback) ---
                    logging.info(f"Attempting API download for: {link}")
                    try:
                        video_id = extract_video_id(link)
                    except ValueError:
                        video_id = None
                        
                    if video_id:
                        downloaded_file = await loop.run_in_executor(None, api_dl, video_id)
                    else:
                        downloaded_file = None
                        
                    if downloaded_file is None:
                        # 2. API မအောင်မြင်မှ yt-dlp ကိုခေါ်
                        downloaded_file = await loop.run_in_executor(None, audio_dl_fallback)
                    # --- END: API-First Logic (Fallback) ---
            # --- END: Audio Download/Stream Logic ---
            
        return downloaded_file, direct
