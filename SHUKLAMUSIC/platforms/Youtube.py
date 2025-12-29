# ---------------------------------------------------------------
# 🔸 Shashank Saavn-API Project (Replaced)
# 🔹 Originally by: Shashank Shukla
# 📅 Updated: 2025
# ---------------------------------------------------------------

import asyncio
import os
import aiohttp
import logging
from typing import Union
from pyrogram.types import Message
from pyrogram.enums import MessageEntityType
from SHUKLAMUSIC import LOGGER

# New API Endpoint
API_BASE_URL = "https://saavnify.qzz.io/api/search/songs"

# Helper to format seconds to MM:SS
def seconds_to_time(seconds):
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"

async def download_saavn_content(query: str, download_type: str = "audio") -> str:
    """
    Searches and downloads the song using Saavnify API.
    """
    logger = LOGGER("StrangerAPI/Saavn.py")
    
    # Clean query if it's a URL
    if "http" in query:
        # If it's a link, we might need to extract a query or handle it differently
        # For now, we assume the user passes a song name or the API handles the link
        pass

    try:
        async with aiohttp.ClientSession() as session:
            # 1. Search for the song
            search_url = f"{API_BASE_URL}?query={query}"
            async with session.get(search_url) as resp:
                if resp.status != 200:
                    logger.error(f"❌ API Error: {resp.status}")
                    return None
                data = await resp.json()

            if not data.get("success") or not data.get("data") or not data["data"]["results"]:
                logger.error("❌ No results found on Saavn.")
                return None

            # Get the first result
            result = data["data"]["results"][0]
            song_id = result["id"]
            title = result["name"]
            
            # Get 320kbps download link (fallback to lower quality if not available)
            download_urls = result.get("downloadUrl", [])
            file_url = None
            
            # Try to find 320kbps, then 160kbps, then last available
            for d in download_urls:
                if d["quality"] == "320kbps":
                    file_url = d["url"]
                    break
            if not file_url and download_urls:
                file_url = download_urls[-1]["url"]

            if not file_url:
                logger.error("❌ No download URL found in API response.")
                return None

            # 2. Download the file
            DOWNLOAD_DIR = "downloads"
            os.makedirs(DOWNLOAD_DIR, exist_ok=True)
            extension = "m4a" # Saavn usually sends m4a/mp4 audio
            file_path = os.path.join(DOWNLOAD_DIR, f"{song_id}.{extension}")

            if os.path.exists(file_path):
                logger.info(f"📂 [LOCAL] File exists: {title}")
                return file_path

            logger.info(f"⬇️ Downloading: {title} from Saavn...")
            async with session.get(file_url) as file_resp:
                if file_resp.status == 200:
                    with open(file_path, 'wb') as f:
                        while True:
                            chunk = await file_resp.content.read(1024)
                            if not chunk:
                                break
                            f.write(chunk)
                    logger.info(f"✅ Download Complete: {file_path}")
                    return file_path
                else:
                    logger.error("❌ Failed to download file stream.")
                    return None

    except Exception as e:
        logger.error(f"❌ Exception in download: {e}")
        return None

# Wrapper functions to maintain compatibility with your bot's logic
async def download_song(link: str) -> str:
    return await download_saavn_content(link, "audio")

async def download_video(link: str) -> str:
    # Saavn is Audio only. We return the audio file even if video is requested.
    # This prevents the bot from crashing.
    return await download_saavn_content(link, "video") 

class YouTubeAPI:
    """
    Renamed logic to use Saavn, but Class name kept same 
    to prevent breaking SHUKLAMUSIC imports.
    """
    def __init__(self):
        self.base = "https://www.jiosaavn.com/song/" # Just for regex checks if needed
        self.regex = r"(?:jiosaavn\.com|saavn\.com)"

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        # Always return True to force search, or implement saavn regex
        return True

    async def url(self, message_1: Message) -> Union[str, None]:
        # Extracts URL or Text from message
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset: entity.offset + entity.length]
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        """
        Returns: Title, Duration(String), Duration(Seconds), Thumbnail, ID
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE_URL}?query={link}") as resp:
                    data = await resp.json()
                    
            if data["success"] and data["data"]["results"]:
                res = data["data"]["results"][0]
                title = res["name"]
                duration_sec = int(res["duration"])
                duration_min = seconds_to_time(duration_sec)
                vidid = res["id"]
                # Get highest quality image
                thumbnail = res["image"][-1]["url"] if res["image"] else ""
                
                return title, duration_min, duration_sec, thumbnail, vidid
            return None, "00:00", 0, "", ""
        except Exception:
            return None, "00:00", 0, "", ""

    async def title(self, link: str, videoid: Union[bool, str] = None):
        t, _, _, _, _ = await self.details(link)
        return t

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        _, d, _, _, _ = await self.details(link)
        return d

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        _, _, _, t, _ = await self.details(link)
        return t

    async def video(self, link: str, videoid: Union[bool, str] = None):
        # Maps to download_song because Saavn has no video
        try:
            downloaded_file = await download_song(link)
            if downloaded_file:
                return 1, downloaded_file
            return 0, "Download failed"
        except Exception as e:
            return 0, f"Error: {e}"

    async def track(self, link: str, videoid: Union[bool, str] = None):
        """
        Returns track_details dict and vidid
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE_URL}?query={link}") as resp:
                    data = await resp.json()

            if data["success"] and data["data"]["results"]:
                res = data["data"]["results"][0]
                
                track_details = {
                    "title": res["name"],
                    "link": res["url"],
                    "vidid": res["id"],
                    "duration_min": seconds_to_time(res["duration"]),
                    "thumb": res["image"][-1]["url"] if res["image"] else "",
                }
                return track_details, res["id"]
            return None, None
        except Exception:
            return None, None

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        # Saavn doesn't return formats like Yt-Dlp. 
        # We return a dummy list to satisfy the bot's expectations.
        return [{"format": "320kbps", "filesize": 0, "ext": "m4a"}], link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        # Fetch results and pick the one at index 'query_type'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE_URL}?query={link}") as resp:
                    data = await resp.json()

            if data["success"] and data["data"]["results"]:
                # Ensure index exists
                idx = query_type if query_type < len(data["data"]["results"]) else 0
                res = data["data"]["results"][idx]
                
                return (
                    res["name"],
                    seconds_to_time(res["duration"]),
                    res["image"][-1]["url"],
                    res["id"]
                )
            return None, None, None, None
        except:
            return None, None, None, None

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
        # Unified download method
        try:
            # We ignore 'video' boolean because Saavn is audio-only.
            # We just download the song.
            downloaded_file = await download_song(link)
            
            if downloaded_file:
                return downloaded_file, True
            else:
                return None, False
        except Exception as e:
            return None, False
