import re
import random
import os
import logging
import json
from os import getenv, makedirs
from pathlib import Path
from aiohttp import ClientSession
from asyncio import sleep as asyncsleep
from moviepy.editor import VideoFileClip
from PIL import Image
from pyrogram import Client, filters, types
from cv2 import VideoCapture, imwrite, CAP_PROP_FRAME_COUNT, CAP_PROP_FPS
from yt_dlp import YoutubeDL
from requests import get
from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs
import urllib

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from config
API_HASH = getenv("API_HASH", "00b7ca7f535e816590db39e76f85d0c7")
API_ID = getenv("API_ID", "28374181")
BOT_TOKEN = getenv("BOT_TOKEN", "8025985068:AAFaA-FmxgZpTZ1Rz0DIHr37faG-AwLu4zU")
CHANNEL_ID = -1002316696001  # Hardcoded channel ID

# Initialize temporary storage for user data
temp = {}

class Porn:
    """
    A class for interacting with the xnxxx.work website.
    """

    def __init__(self):
        """
        Initialize the Porn class with the base URL.
        """
        self.base_url = "https://xnxxx.work"

    @staticmethod
    def get_token(length: int = 6) -> str:
        """ Returns 6 unique characters """
        characters = string.ascii_letters
        token = "".join(random.choice(characters) for _ in range(length))
        return token

    @staticmethod
    def quote(text: str) -> str:
        """ Convert the text to Url safe string """
        quote = urllib.parse.quote(text)
        return quote

    @staticmethod
    def get_header() -> dict:
        """
        Generate a random User-Agent header.

        Returns:
            dict: A dictionary containing the User-Agent header.
        """
        user_agent = UserAgent()
        headers = {"User -Agent": user_agent.random}
        return headers

    @staticmethod
    async def download(download_url: str, filename: str = None) -> dict:
        """
        Download a file using the wget module.

        Args:
            download_url (str): The URL of the file to download.

        Returns:
            dict: A dictionary containing the file path.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(download_url)
                if response.status_code != 200:
                    return {"error": f"❌ ERROR: Status {str(response.status_code)}"}
                content = response.read()

                if filename is None:
                    filename = str(uuid.uuid4()) + ".mp4"
                with open(filename, "wb+") as file:
                    file.write(content)
                return {"path": os.path.abspath(filename)}
        except Exception as error:
            return {"error": f"❌ ERROR:\n{str(error)}"}

    async def get_download_url(self, url: str) -> str:
        """
        Get the downloadable URL for a video.

        Args:
            url (str): The URL of the video page.

        Returns:
            str: The downloadable URL or an error message.
        """
        try:
            async with httpx.AsyncClient() as session:
                response = await session.get(url, headers=self.get_header())
                if response.status_code != 200:
                    return {"error": f"❌ ERROR:\n Status {str(response.status_code)}"}
                soup = bs(response.text, "html.parser")
                try:
                    source = soup.find_all("div", class_="video")[0].find("source").get("src")
                except Exception as error:
                    return {"error": f"❌ Cant fetch download url ERROR: {error}"}
                return {"download_url": source}

        except Exception as error:
            return {"error": f"❌ Cant fetch download url ERROR: {error}"}

    async def search(self, query: str) -> list:
        """
        Search for videos on the xnxxx.work website.

        Args:
            url (str): The URL of the search page.

        Returns:
            list: A list of video metadata dictionaries.
        """
        url = f"https://xnxxx.work/bigtits-fuck?query={self.quote(query)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.get_header()) as response:
                if response.status != 200:
                    return [{"error": f"can't fetch data from {url} reason: {response.reason}"}]
                soup = bs(await response.text(), "html.parser")
                video_data = soup.find(class_="thumbs").find_all('li')
                formatted_data = [
                    {
                        "thumb": video.img["data-src"],
                        "preview": video.find(class_="thumb-img").get("data-preview-url"),
                        "title": video.p.text,
                        "link": video.a.get("href"),
                        "duration": video.find(class_="th-time").text
                    } for video in video_data
                ]
                return formatted_data

# Define the plugin functions
async def resize_image(path: str):
    img = Image.open(path)
    img.thumbnail((320, 240))  # Resize to 320x240
    img.save(path)

async def delete_results_after_delay(user_id, delay=600):
    await asyncsleep(delay)
    if user_id in temp:
        del temp[user_id]
        logging.info(f"Deleted results for user {user_id} after {delay} seconds.")

async def mydata(client: Client, message: types.Message):
    user = message.from_user
    if user.id in temp:
        data = temp[user.id]
        path = f"{user.full_name}_data.json"
        with open(path, "w+") as file:
            file.write(json.dumps(data[1]))
        await message.reply_document(document=path, caption=f"**{user.full_name}'s search data**")
    else:
        return await message.reply("I don't have any of your data yet.")

async def reply(client: Client, message: types.Message):
    return await message.reply_text("/search hot sexy girl")

async def callback_query(client: Client, query: types.CallbackQuery):
    query_data = query.data
    user = query.from_user

    if query_data.startswith("show"):
        _, CQtoken, CQindex = query_data.split(":")
        if user.id not in temp:
            return await query.answer("You haven't registered any search though!", show_alert=True)

        token, results = temp[user.id]

        if CQtoken != token:
            return await query.answer("This Query is expired please search again..", show_alert=True)

        result = results[int(CQindex)]
        await query.message.reply_text(str(result))

    elif query_data.startswith("download"):
        await handle_download(query, user)

    elif query_data.startswith("preview"):
        await handle_preview(query, user)

async def handle_download(query, user):
    # Implement the download logic here
    # After sending the results, start the deletion timer
    await delete_results_after_delay(user.id)

async def handle_preview(query, user):
    # Implement the preview logic here
    # After sending the results, start the deletion timer
    await delete_results_after_delay(user.id)

async def search(client: Client, message: types.Message):
    msg_txt = message.text
    user = message.from_user

    # Check if user is in the channel
    try:
        await client.get_chat_member("@Venuma", user.id)
    except Exception as e:
        return await message.reply_text("😜 **Join @Venuma to use /search baby** 👻\n```python\n{error}```".format(error=str(e)))

    if len(msg_txt.split()) < 2:
        return await message.reply("```\n/search query```\n**Use this format to search though!**")
    else:
        query = message.text.split(maxsplit=1)[1]
        results = await porn.search(query)
        token = porn.get_token()

        if 'error' in results:
            return await message.reply(results['error'])

        if user.id in temp:
            await message.reply("**🗑️ Cleared your previous query search data results...**", quote=True)

        temp[user.id] = token, results
        query, results = temp[user.id]

        result = results[0]
        index = 0
        caption = (
            f"😍 **Name**: 😜 {result['title']}"
            f"\n⏳ **Total Duration**: 👄 {result['duration']}"
            f"\n🗂️ **Index no**: {index}"
        )

        button = types.InlineKeyboardMarkup(
            [
                [
                    types.InlineKeyboardButton("Next ⏭️", callback_data=f"next:{token}:{index}"),
                ],
                [
                    types.InlineKeyboardButton("Preview 😋", callback_data=f"preview:{token}:{index}"),
                    types.InlineKeyboardButton("Data 📩", callback_data=f"show:{token}:{index}"),
                ],
                [
                    types.InlineKeyboardButton("Download 👅", callback_data=f"download:{token}:{index}")
                ]
            ]
        )

        await message.reply_photo(
            photo=result['thumb'],
            caption=caption,
            reply_markup=button,
            quote=True
        )

# Video processing functions
def extract_seconds(file: str) -> int:
    VIDEO = VideoCapture(file)  # RUTA DEL VIDEO
    frames = VIDEO.get(CAP_PROP_FRAME_COUNT)
    fps = int(VIDEO.get(CAP_PROP_FPS))
    return int(frames / fps)

def extract_img(file: str, message: types.Message) -> list:
    try:
        makedirs(join(message.from_user.username, "IMG"))
    except:
        pass

    VIDEO = VideoCapture(file)
    total_frames = int(VIDEO.get(CAP_PROP_FRAME_COUNT))
    result = total_frames // 10

    count = 1
    img_list = []

    for i in range(result // 2, total_frames, result):
        VIDEO.set(CAP_PROP_POS_FRAMES, i)
        frame = VIDEO.read()[1]
        imwrite(f"./{message.from_user.username}/IMG/IMG-{count}.jpg", frame)
        img_list.append(types.InputMediaPhoto(join(message.from_user.username, "IMG", f"IMG-{count}.jpg")))
        count += 1

    return img_list

def download(url: str) -> str:
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
    }
    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url)
        video_filename = ydl.prepare_filename(info_dict)
        with open(info_dict['title'] + '.jpeg', 'wb') as f:
            f.write(get(info_dict['thumbnail']).content)
        return video_filename, info_dict['title'] + '.jpeg'

# Register the handlers with the bot
def register_handlers(client: Client):
    client.add_handler(filters.command("mydata")(mydata))
    client.add_handler(filters.private & ~filters.command(["search", "mydata"])(reply))
    client.add_handler(filters.command("search")(search))
    client.add_handler(filters.callback_query()(callback_query))
