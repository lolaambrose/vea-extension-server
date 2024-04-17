from html import escape
import json
import os

from platformdirs import user_cache_dir
from logger import logger
import config

from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ParseMode
from aiogram.filters.command import Command, CommandObject
from datetime import datetime, timedelta, timezone

dp = Dispatcher()


async def start():
    logger.info("starting...")

    global chatbot
    chatbot = Bot(config.TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)

    await dp.start_polling(chatbot)


@dp.message(Command("start"))
async def command_start(message: types.Message):
    await message.reply(
        "👋 <b>Добро пожаловать в бот мониторинга действий чаттеров Vea!</b>"
    )


def convert_timestamp_to_date(timestamp):
    try:
        # Преобразование миллисекунд в секунды
        timestamp = float(timestamp) / 1000
        date_time = datetime.fromtimestamp(timestamp)
        readable_date = date_time.strftime("%Y-%m-%d %H:%M:%S")
        return readable_date
    except ValueError:
        logger.error(f"Некорректный timestamp: {timestamp}")
        return "некорректная дата"


async def send_banword_attempt(data: dict):
    banword = escape(data["banword"])
    username = escape(data["username"])
    login_time = convert_timestamp_to_date(data["login_time"])
    for admin in config.TELEGRAM_ADMINS:
        await chatbot.send_message(
            chat_id=admin,
            text=f"⚠️ <b>Чаттер пытался отправить запрещенное слово</b>\n├ <code>{banword}</code>\n├ <b>Аккаунт</b> onlyfans.com/{username}\n└ <b>Время логина</b> <code>{login_time}</code>",
        )


async def send_uninstall_attempt(data: dict):
    username = data["username"]
    login_time = convert_timestamp_to_date(data["login_time"])

    for admin in config.TELEGRAM_ADMINS:
        await chatbot.send_message(
            chat_id=admin,
            text=f"🦹 <b>Чаттер пытался удалить расширение</b>\n├ <b>Аккаунт</b> onlyfans.com/{username}\n└ <b>Время логина</b> <code>{login_time}</code>",
        )


async def send_long_message(chat_id, text, max_length=4096):
    while text:
        # Отправляем часть текста, не превышающую максимально допустимую длину
        part = text[:max_length]
        await chatbot.send_message(chat_id=chat_id, text=part)
        # Удаляем отправленную часть из текста
        text = text[max_length:]


@dp.message(Command("banwords_show"))
async def banwords_show(message: types.Message, command: CommandObject):
    if not message.from_user:
        return

    admin_ids = config.TELEGRAM_ADMINS
    if message.from_user.id not in admin_ids:
        await message.reply("🚫 <b>У вас нет прав для выполнения этой команды.</b>")
        return

    file = None
    try:
        file = open("banwords.txt", "r")
        banwords = file.read()
        banwords_list = banwords.split()
        formatted_banwords = "\n".join([f"├ {word}" for word in banwords_list])
        await send_long_message(
            message.chat.id,
            f"🔴 <b>Запрещенные слова</b>\n{formatted_banwords}",
        )
    except FileNotFoundError:
        await message.reply("🔎 <b>Файл с запрещенными словами не найден.</b>")
    finally:
        if file:
            file.close()


@dp.message(Command("banwords_upload"))
async def banwords_upload(message: types.Message, command: CommandObject):
    if not message.from_user:
        return

    admin_ids = config.TELEGRAM_ADMINS
    if message.from_user.id not in admin_ids:
        await message.reply("🚫 <b>У вас нет прав для выполнения этой команды.</b>")
        return

    if not message.document:
        await message.reply("📁 <b>Пожалуйста, прикрепите файл.</b>")
        return

    document_id = message.document.file_id
    file = await chatbot.get_file(document_id)
    file_path = file.file_path

    valid_extensions = [".txt"]
    if file_path is None or not any(
        file_path.endswith(ext) for ext in valid_extensions
    ):
        await message.reply(
            "⚠️ <b>Неверный формат файла.</b> Пожалуйста, загрузите файл в формате <i>.txt</i>"
        )
        return

    file_contents = await chatbot.download_file(file_path)
    correct_format = False  # Инициализация переменной перед использованием
    if file_contents:
        content_str = file_contents.read()
        if content_str:
            correct_format = all(
                [
                    word.strip().startswith('"') and word.strip().endswith('"')
                    for word in content_str.decode().split(",")
                ]
            )
        if not correct_format:
            await message.reply(
                '⚠️ <b>Неверный формат содержимого файла.</b> Файл должен содержать слова в формате <code>"text1", "text2", "text3"...</code>'
            )
            return

        with open("banwords.txt", "wb") as new_file:
            new_file.write(content_str)
        await message.reply("✅ <b>Файл успешно загружен.</b>")
    else:
        await message.reply("😢 <b>Не удалось загрузить файл.</b>")


@dp.message(Command("add_admin"))
async def add_admin(message: types.Message):
    if not message.from_user or not message.text:
        return

    admin_ids = config.TELEGRAM_ADMINS
    if message.from_user.id not in admin_ids:
        await message.reply("🚫 <b>У вас нет прав для выполнения этой команды.</b>")
        return

    try:
        new_admin_id = int(message.text.split()[1])  # Получаем ID из сообщения
        if new_admin_id and new_admin_id not in admin_ids:
            admin_ids.append(new_admin_id)
            os.environ["TELEGRAM_ADMINS"] = json.dumps(
                admin_ids
            )  # Обновляем переменную среды
            await message.reply(
                f"✅ <b>Новый админ с ID {new_admin_id} успешно добавлен.</b>"
            )
        else:
            await message.reply(
                "⚠️ <b>Пожалуйста, укажите корректный ID или ID уже добавлен.</b>"
            )
    except (ValueError, IndexError):
        await message.reply("⚠️ <b>ID должен быть числом и указан после команды.</b>")


@dp.message(Command("remove_admin"))
async def remove_admin(message: types.Message):
    if not message.from_user or not message.text:
        return

    admin_ids = config.TELEGRAM_ADMINS
    if message.from_user.id not in admin_ids:
        await message.reply("🚫 <b>У вас нет прав для выполнения этой команды.</b>")
        return

    try:
        admin_id_to_remove = int(message.text.split()[1])  # Получаем ID из сообщения
        if admin_id_to_remove and admin_id_to_remove in admin_ids:
            admin_ids.remove(admin_id_to_remove)
            os.environ["TELEGRAM_ADMINS"] = json.dumps(
                admin_ids
            )  # Обновляем переменную среды
            await message.reply(
                f"✅ <b>Админ с ID {admin_id_to_remove} успешно удален.</b>"
            )
        else:
            await message.reply(
                "⚠️ <b>Пожалуйста, укажите корректный ID или ID не найден среди админов.</b>"
            )
    except (ValueError, IndexError):
        await message.reply("⚠️ <b>ID должен быть числом и указан после команды.</b>")
