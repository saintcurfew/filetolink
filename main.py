from contextlib import suppress
from math import floor
from os import remove
from secrets import token_hex
from sys import exit as exiter
from time import time

import boto3
from pyrogram import Client
from pyrogram.errors import MessageNotModified, RPCError
from pyrogram.filters import command, document, photo, poll, private, regex, user, video
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from redis.asyncio import Redis
from redis.exceptions import RedisError
from requests import get
from requests.exceptions import Timeout

ENDPOINT = "https://ba9816a848610aed92b1359ca60ff37a.r2.cloudflarestorage.com/"
ACCESS_KEY = "24c2515db578726cd36ea0772946474b"
SECRET_KEY = "b79167444ad27359f7e587bff2bf72bea9003add5a6411d0ce98276645133e36"
APP_URL = "https://dumpstore.online"
app2 = Client(
    "bot",
    2992000,
    "235b12e862d71234ea222082052822fd",
    bot_token="5642095585:AAFZbW1-2asinNkp_Qd53Jni8rnWPFnRF10",
)

msg = []
REDIS = Redis.from_url(
    "redis://default:4EfI0X4V6Xg8ESmLQJXhp6vAQvjkBchJ@redis-18376.c264.ap-south-1-1.ec2.cloud.redislabs.com:18376",
    decode_responses=True,
)

try:
    app2.loop.run_until_complete(REDIS.ping())
    print("Your redis server is alive!")
except RedisError:
    exiter("Your redis server is not alive, please check again!")


async def short_link(slink: str, api: str):
    try:
        r = get(f"https://reduxplay.com/api?api={api}&url={slink}",
                stream=True,
                timeout=10)
        response = r.json()
        if response["status"] == "error":
            return f"error: {response['message']}"
    except ConnectionError as e:
        return f"error: {e}"
    return response["shortenedUrl"]


@app2.on_message(command("token") & private)
async def adoken(_: app2, m: Message):
    data = m.text.split()
    if len(data) < 2:
        if da := await REDIS.get(f"_{m.from_user.id}"):
            await m.reply_text(f"Currently added shortner api key is: {da}")
            return
        await m.reply_text(
            "Provide a api key to add for short links from reduxplay.com!")
        return
    await addtoken(m, data[1])
    return


@app2.on_message(command("rmtoken") & private)
async def rmtoken(_: app2, m: Message):
    if await REDIS.get(f"_{m.from_user.id}"):
        await REDIS.delete(f"_{m.from_user.id}")
        await m.reply_text("Deleted!")
        return
    await m.reply_text(
        "No shortener api key has been added by you to remove in my database!")
    return


async def addtoken(m: Message, data: str):
    dat = await short_link("https://www.github.com/annihilatorrrr", data)
    if dat.startswith("error: "):
        await m.reply_text(dat)
        return
    await REDIS.set(f"_{m.from_user.id}", data)
    await m.reply_text("Your shortener API is now Connected.✅")
    return


def genetare_key():
    return token_hex(4)


async def progress_for_pyrogram(
    current: float,
    total: float,
    ud_type: str,
    message: Message,
    start: float,
):
    if message.id in msg:
        app2.stop_transmission()
        msg.pop(message.id)
        return
    diff = time() - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = TimeFormatter(milliseconds=elapsed_time +
                                             time_to_completion)

        progress = "[{0}{1}] \n**Process**: {2}%\n".format(
            "".join(("◆" for _ in range(floor(percentage / 5)))),
            "".join(("◇" for _ in range(20 - floor(percentage / 5)))),
            round(percentage, 2),
        )

        tmp = progress + "{0} of {1}\n**Speed:** {2}/s\n**ETA:** {3}\n".format(
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            estimated_total_time if estimated_total_time != "" else "0 s",
        )
        try:
            await message.edit_text(
                text="{}\n {}".format(ud_type, tmp),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Cancel",
                                           callback_data="cancel")]]),
            )
        except:
            pass


def humanbytes(size: float):
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: " ", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti"}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + "B"


def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (((str(days) + "d, ") if days else "") +
           ((str(hours) + "h, ") if hours else "") +
           ((str(minutes) + "m, ") if minutes else "") +
           ((str(seconds) + "s, ") if seconds else "") +
           ((str(milliseconds) + "ms, ") if milliseconds else ""))
    return tmp[:-2]


class CloudStorage:

    def __init__(self, file: str = None):
        self.s3 = boto3.resource(
            "s3",
            endpoint_url=ENDPOINT,
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
        )
        self.file = file
        self.bucket = self.s3.Bucket("f2lstorage")

    def upload(self):
        token = f"{genetare_key()}/{self.file.split('/')[-1].replace(' ', '.')}"
        try:
            self.bucket.upload_file(self.file, token)
        except:
            return None
        return f"{APP_URL}/{token}"

    def delete(self, token: str):
        if not self.check_url(token):
            return False
        self.bucket.objects.filter(Prefix=token).delete()
        return True

    def check_url(self, token: str):
        try:
            if get(f"{APP_URL}/{token}", timeout=2).status_code == 404:
                return False
        except Timeout:
            return False
        return True

    def delete_all(self):
        self.bucket.objects.all().delete()


@app2.on_message(command("start") & private)
async def startm(_, m: Message):
    await m.reply_text(
        "Send Me a File and I will send You a link for it.\n\nIts that simple."
    )

    return


@app2.on_message(~poll & private & photo | video | document)
async def download(c: app2, m: Message):
    key = await REDIS.get(f"_{m.from_user.id}")
    if not key:
        await m.reply_text(
            "Add the api key from reduxplay.com in my database first!")
        return
    msg1 = await m.reply_text(
        "Downloading...",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Cancel", callback_data="cancel")]]),
    )
    file = 0
    try:
        file = await m.download(
            progress=progress_for_pyrogram,
            progress_args=("Downloading to server...", msg1, time()),
        )
    except (RPCError, MessageNotModified):
        pass
    if not file:
        await msg1.edit_text("Error: file wasn't downloaded!")
        return
    await msg1.edit_text("Uploading to server..")
    cloud = CloudStorage(file).upload()
    with suppress(RPCError):
        await app2.copy_message(
            -1001883346027,
            m.chat.id,
            m.id,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔗 Download link", url=cloud)]]),
        )
    with suppress(OSError):
        remove(file)
    if not cloud:
        await msg1.edit_text("Something went wrong!")
        return
    slink = await short_link(cloud, key)
    if slink.startswith("error: "):
        await m.reply_text(slink)
        return
    thub = 0
    if m.document and len(m.document.thumbs) >= 1:
        thub = m.document.thumbs[0].file_id
    elif m.video and len(m.video.thumbs) >= 1:
        thub = m.video.thumbs[0].file_id
    elif m.photo and len(m.photo.thumbs) >= 1:
        thub = m.photo.thumbs[0].file_id
    if thub:
        await msg1.delete()
        dn = await c.download_media(thub)
        await m.reply_photo(
            dn,
            caption=f"Your file is ready:\n\n `{slink}`",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔗 Download link", url=slink)]]),
        )
        remove(dn)
    else:
        await msg1.edit_text(
            f"Your file is ready:\n\n `{slink}`",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔗 Download link", url=slink)]]),
        )
    return


@app2.on_message(command("delete") & user([683684279, 5205492927, 2107137268]))
async def delete(_, m: Message):
    if len(m.command) == 2:
        token = m.command[1].replace(f"{APP_URL}/", "")
        delet = CloudStorage().delete(token)
        if not delet:
            return await m.reply_text("File not found!")
        return await m.reply_text("File deleted successfully!")
    else:
        return await m.reply_text("Please provide a token!")


@app2.on_message(
    command("deleteall") & user([683684279, 5205492927, 2107137268]))
async def deleteall(_, m: Message):
    CloudStorage().delete_all()
    await m.reply_text("All files deleted successfully!")
    return


@app2.on_callback_query(regex("cancel"))
async def cancel(_, c: CallbackQuery):
    await c.message.edit_text("Cancelled!")
    msg.append(c.message.id)
    return


print("Started!")
app2.run()
print("Bye!")
