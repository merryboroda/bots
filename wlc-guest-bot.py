from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from netmiko import ConnectHandler
from datetime import datetime, timedelta
import random
import string
import logging

TELEGRAM_TOKEN = "token"
WLC_HOST = "ip_address"
WLC_USERNAME = "username"
WLC_PASSWORD = "password"
SSID = "ssid"
ACCOUNT_DURATION_DAYS = 1

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Генерация случайного пароля
def generate_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Создание гостевой учетной записи
def create_guest_account(custom_name: str):
    # Проверяем корректность имени
    if not custom_name.isalnum():
        return None, None, None, "Имя может содержать только буквы и цифры."

    # Добавляем префикс "guest_"
    username = f"guest_{custom_name}"
    password = generate_password()

    # Вычисляем срок действия учетной записи
    expiration_date = (datetime.now() + timedelta(days=ACCOUNT_DURATION_DAYS)).strftime('%m/%d/%Y')

    # Команда для создания учетной записи
    commands = [
        f"config netuser add {username} {password} wlan 2 userType guest lifetime 86400 description Guest"
    ]

    # Параметры подключения к Cisco WLC через Netmiko
    wlc = {
        "device_type": "cisco_wlc",
        "host": WLC_HOST,
        "username": WLC_USERNAME,
        "password": WLC_PASSWORD,
    }

    try:
        # Подключение к Cisco WLC и выполнение команд
        connection = ConnectHandler(**wlc)
        for command in commands:
            connection.send_command(command)
        connection.disconnect()
        return username, password, expiration_date, None
    except Exception as e:
        logger.error(f"Ошибка подключения: {e}")
        return None, None, None, "Ошибка подключения к Cisco WLC."


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Я бот для создания гостевых учетных записей.\n"
        "Введите /create <имя>, чтобы создать новую учетную запись."
    )


# Команда /create
async def create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 0:
        await update.message.reply_text(
            "Пожалуйста, укажите имя для учетной записи после команды. Например: /create Ivan")
        return

    custom_name = context.args[0]
    await update.message.reply_text("Создаю учетную запись...")

    username, password, expiration_date, error = create_guest_account(custom_name)

    if error:
        await update.message.reply_text(f"Ошибка: {error}")
    elif username and password:
        await update.message.reply_text(
            f"Гостевая учетная запись создана!\n"
            f"SSID: {SSID}\n"
            f"Имя пользователя: {username}\n"
            f"Пароль: {password}\n"
            f"Срок действия: до {expiration_date}"
        )
    else:
        await update.message.reply_text("Не удалось создать учетную запись. Попробуйте позже.")


# Основная функция для запуска бота
def main():
    # Создаем приложение бота
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("create", create))

    # Запуск бота
    application.run_polling()


if __name__ == "__main__":
    main()
