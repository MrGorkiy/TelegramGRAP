import json
import os
import re

import requests
import vk_api
from telethon import TelegramClient, events
from vk_api.upload import VkUpload
from vk_api.utils import get_random_id

from confing import *

# Подключаемся к ВК
vkontakte = vk_api.VkApi(token=VK_TOKEN)
api_vkontakte = vkontakte.get_api()

# каналы откуда берем сообщения
CHANNELS = ["@bolshenews", -1001708761316]

# заменяем нежелательные выражения, перед пересылкой, можно использовать регулярки
KEYS = {
    r"@\S+": "@неважно",
    r"https://\S+": f"vk.com/club{GROUP_ID}",
    r"t.me/\S+": f"vk.com/club{GROUP_ID}",
    r"http://\S+": f"vk.com/club{GROUP_ID}",
    "Новости": "Последние события",
}

# СТОП СЛОВО - не будем публиковать если содержится (частичное совпадение)
BAD_KEYS = [
    "ставки",
    "каналом",
    "создан",
    "канал",
    "бот",
    "подписаться",
]
# СТОП СЛОВО - не будем публиковать если содержится (точное совпадение)
OWE_BAD = ['бот', 'бота']


def metod_vk_api(metod, params):
    requests.get(
        f"https://api.vk.com/method/{metod}?"
        f"&access_token={VK_TOKEN_APPLICATION}&v={V}",
        params=params,
    ).json()


def save_r(upload_response):
    save_result = requests.get(
        "https://api.vk.com/method/photos.saveWallPhoto?",
        params={
            "access_token": VK_TOKEN_SELF,
            "group_id": GROUP_ID,
            "photo": upload_response["photo"],
            "server": upload_response["server"],
            "hash": upload_response["hash"],
            "v": V,
        },
    ).json()
    return (
            "photo"
            + str(save_result["response"][0]["owner_id"])
            + "_"
            + str(save_result["response"][0]["id"])
    )


def inspect_list(list1, list2):
    return list(set(list1) & set(list2))


def upload_loc_photo(upload, url):
    response = upload.photo_messages(url)[0]

    owner_id = response["owner_id"]
    photo_id = response["id"]
    access_key = response["access_key"]

    return f"photo{owner_id}_{photo_id}_{access_key}"


def getwalluploadserver():
    """Получаем ссылку для загрузки видео в ВК"""
    rq = requests.get(
        "https://api.vk.com/method/video.save?",
        params={
            "access_token": VK_TOKEN_SELF,
            "group_id": GROUP_ID,
            "is_private": 1,
            "name": "Без имени",
            "v": V,
        },
    ).json()
    return {"upload_url": rq["response"]["upload_url"]}


def getwallphoto():
    rq = requests.get(
        "https://api.vk.com/method/photos.getWallUploadServer?",
        params={"access_token": VK_TOKEN_SELF, "group_id": GROUP_ID, "v": V},
    ).json()
    return rq["response"]["upload_url"]


def save_video(upload_response):
    """Из ответа формируем attachments для отправки сообщением"""
    return f'video{upload_response["owner_id"]}_{upload_response["video_id"]}'


def message_send(peer_id, text=None, keyboard=None,
                 attachment=None, forward=None):
    """Отправка сообщения по peer_id, без уведомления в чате"""
    post = {
        "peer_id": peer_id,
        "random_id": get_random_id(),
        "disable_mentions": 1,
    }

    if text:
        post["message"] = text
    if keyboard:
        post["keyboard"] = keyboard
    if attachment:
        post["attachment"] = attachment
    if forward:
        post["forward"] = [
            json.dumps(
                {
                    "peer_id": peer_id,
                    "conversation_message_ids": [forward],
                    "is_reply": True,
                }
            )
        ]
    vkontakte.method("messages.send", post)


def wall_post(message=None, attachments=None):
    param = {'owner_id': '-' + str(GROUP_ID),
             'from_group': 1}
    if message:
        param['message'] = message
    if attachments:
        param['attachments'] = attachments

    metod_vk_api("wall.post", param)


def correct_context(path, text=None):
    """
    Если вложение фото или видео, скачиваю,
    загружаю в ВК, отправляю и удаляю
    """
    if path[-3:] == "mp4":
        upload = getwalluploadserver()
        file = {"file1": open(path, "rb")}
        upload_response = requests.post(upload["upload_url"],
                                        files=file).json()
        file["file1"].close()
        if text:
            # message_send(PEER_CHAT, text=text,
            #              attachment=save_video(upload_response))
            wall_post(message=text, attachments=save_video(upload_response))
        else:
            # message_send(PEER_CHAT, attachment=save_video(upload_response))
            wall_post(attachments=save_video(upload_response))
    elif path[-3:] == "jpg":
        upload = getwallphoto()
        file = {"file1": open(path, "rb")}
        upload_response = requests.post(upload, files=file).json()
        file["file1"].close()
        if text:
            # message_send(PEER_CHAT, text=text,
            #              attachment=upload_loc_photo(upload, path))
            wall_post(message=text, attachments=save_r(upload_response))
        else:
            # message_send(PEER_CHAT, attachment=upload_loc_photo(upload, path))
            wall_post(attachments=save_r(upload_response))
    os.remove(path)


with TelegramClient("TelegramBOT", API_ID_TG, API_HASH_TG) as client:
    client.start()  # если включена 2FA то передаем пароль (password='пароль')
    print("Бот запустился, полет нормальный")


    @client.on(events.NewMessage(chats=CHANNELS))
    async def messages(event):
        # print('event: ', event)  # для отладки

        if (not [element for element in BAD_KEYS if
                 event.raw_text.lower().__contains__(element)]
                and not inspect_list(event.raw_text.lower().split(' '),
                                     OWE_BAD)):
            text = event.raw_text
            for i in KEYS:
                text = re.sub(i, KEYS[i], text)

            if (event.message.text and not event.message.media
                    and not event.message.forward and not event.grouped_id):
                print("\nОтправка текста: ", text[:100], "\n")
                # message_send(PEER_CHAT, text)
                wall_post(message=text)

            elif not event.grouped_id and not event.message.forward:
                path = await event.download_media(file="files/img")
                # print('Media: ', event.message.media)
                # print('File saved to', path)
                print("\nОтправка одного вложения: ", text[:100], "\n")
                if path:
                    if not text:
                        correct_context(path)
                    else:
                        correct_context(path, text)
                else:
                    # message_send(PEER_CHAT, text=text)
                    wall_post(message=text)

            elif event.message.forward and not event.grouped_id:
                path = await event.download_media(file="files/img")
                print("\nПерессылка: ", text[:100], "\n")
                if path:
                    if not text:
                        correct_context(path)
                    else:
                        correct_context(path, text)
                else:
                    # message_send(PEER_CHAT, text=text)
                    wall_post(message=text)
            else:
                print("\nИгронирую: ", text[:300], "\n")
        else:
            text = (f'Игнорирую по ключу: \n'
                    f'{[element for element in BAD_KEYS if event.raw_text.lower().__contains__(element)] + inspect_list(event.raw_text.lower().split(" "), OWE_BAD)}'
                    f'\n {event.raw_text}')
            print(text)

    @client.on(events.Album(chats=CHANNELS))
    async def album(event):
        text = event.original_update.message.message
        if not text:
            text = event.raw_text
        # print('text: ', text)
        if (not [element for element in BAD_KEYS if
                 event.raw_text.lower().__contains__(element)]
                and not inspect_list(event.raw_text.lower().split(' '),
                                     OWE_BAD)):
            for i in KEYS:
                text = re.sub(i, KEYS[i], text)

            attachments = []
            for message in event:
                # print('Media: ', message.media)
                path = await message.download_media(file="files/img")
                if path:
                    if path[-3:] == "mp4":
                        upload = getwalluploadserver()
                        file = {"file1": open(path, "rb")}
                        upload_response = requests.post(upload["upload_url"],
                                                        files=file).json()
                        file["file1"].close()
                        attachments.append(save_video(upload_response))
                    elif path[-3:] == "jpg":
                        upload = getwallphoto()
                        file = {"file1": open(path, "rb")}
                        upload_response = requests.post(upload,
                                                        files=file).json()
                        attachments.append(save_r(upload_response))
                        file["file1"].close()
                    os.remove(path)
            print("\nОтправка множества вложений: ", text[:100], "\n\n")
            if text:
                # message_send(PEER_CHAT, text=text,
                #              attachment=",".join(attachments))
                wall_post(message=text, attachments=",".join(attachments))
            else:
                # message_send(PEER_CHAT, attachment=",".join(attachments))
                wall_post(attachments=",".join(attachments))
        else:
            text = (f'Игнорирую по ключу: \n'
                    f'{[element for element in BAD_KEYS if event.raw_text.lower().__contains__(element)] + inspect_list(event.raw_text.lower().split(" "), OWE_BAD)}'
                    f'\n {event.raw_text}')
            print(text)

    client.run_until_disconnected()
