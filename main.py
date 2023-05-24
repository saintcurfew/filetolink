from contextlib import suppress
from os import remove
from secrets import token_hex
import math
import time
import boto3
from pyrogram import Client, filters
from pyrogram.errors import RPCError, MessageNotModified
from pyrogram.filters import media, poll, private, user
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup


ENDPOINT = "https://ba9816a848610aed92b1359ca60ff37a.r2.cloudflarestorage.com/"
ACCESS_KEY = "24c2515db578726cd36ea0772946474b"
SECRET_KEY = "b79167444ad27359f7e587bff2bf72bea9003add5a6411d0ce98276645133e36"
APP_URL = "https://pub-017372d957bd43e39520ad15aed7d2be.r2.dev"
app2 = Client("bot", 2992000, "235b12e862d71234ea222082052822fd",
              bot_token="5822153402:AAGcbKRO1aKU2zsvRNDHRw3YKHsP6uJb6X0")


def genetare_key():
    return token_hex(4)


async def progress_for_pyrogram(
    current,
    total,
    ud_type,
    message,
    start
):
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "[{0}{1}] \n**Process**: {2}%\n".format(
            ''.join(["◆" for i in range(math.floor(percentage / 5))]),
            ''.join(["◇" for i in range(20 - math.floor(percentage / 5))]),
            round(percentage, 2))

        tmp = progress + "{0} of {1}\n**Speed:** {2}/s\n**ETA:** {3}\n".format(
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            estimated_total_time if estimated_total_time != '' else "0 s"
        )
        try:
            await message.edit(
                text="{}\n {}".format(
                    ud_type,
                    tmp
                )
            )
        except:
            pass


def humanbytes(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'


def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
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
        token = f"{genetare_key()}/{self.file.split('/')[-1]}"
        self.bucket.upload_file(self.file, token)
        return f"{APP_URL}/{token}"


@app2.on_message(filters.command("start") & private)
async def start(_, m: Message):
    await m.reply_text(
        "Send Me a File and I will send You a link for it.\n\nIts that simple. 😄\nPowered by : @MAK_Dump"
    )
    return


@app2.on_message(~poll & private & media)
async def download(_, m: Message):
    msg1 = await m.reply_text("Downloading...")
    try:
        file = await m.download(progress=progress_for_pyrogram, progress_args=("Downloading...", msg1, time.time()))
    except (RPCError, MessageNotModified):
        pass
    await msg1.edit("Uploading to cloudflare R2 storage...")
    await m.forward(-1001883346027)
    cloud = CloudStorage(file).upload()
    with suppress(OSError):
        remove(file)
    await msg1.edit(f"Your file is ready:\n\n `{cloud}`", reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔗 Download link", url=cloud)]]
    ))


print("Started!")
app2.run()
print("Bye!")
