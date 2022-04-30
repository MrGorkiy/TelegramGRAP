from telethon import TelegramClient

from confing import *

"""Пару раз возникала трудность активировать токен в рабочем файле,
поэтому использовал это для первого запуска."""
client = TelegramClient("TelegramBOT", API_ID, API_HASH)
client.start()  # если включена 2FA то переадем пароль (password='пароль')
