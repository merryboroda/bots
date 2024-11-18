from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from netmiko import ConnectHandler
from datetime import datetime, timedelta
import random
import string
import logging

TELEGRAM_TOKEN = "token"

WLC_HOST = "ip_address"
WLC_USERNAME = "admin"
WLC_PASSWORD = "password"

SSID = "ssid"
ACCOUNT_DURATION_DAYS = 1

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Функция для генерации случайного пароля
def generate_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Функция для создания гостевой учетной записи на Cisco WLC
def create_guest_account():
    # Генерация уникального имени пользователя и пароля
    username = f"guest_{datetime.now().strftime('%d%m%H%M')}"
    password = generate_password()

    # Вычисление срока действия учетной записи
    expiration_date = (datetime.now() + timedelta(days=ACCOUNT_DURATION_DAYS)).strftime('%m/%d/%Y')

    # Команда для создания гостевой учетной записи
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
        return username, password, expiration_date
    except Exception as e:
        logger.error(f"Ошибка подключения: {e}")
        return None, None, None

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Я бот для создания гостевых учетных записей. Введите /create для создания новой учетной записи.")

# Команда /create
async def create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Создаю учетную запись...")

    username, password, expiration_date = create_guest_account()
    if username and password:
        await update.message.reply_text(
            f"Гостевая учетная запись создана!\nSSID: {SSID}\nИмя пользователя: {username}\nПароль: {password}\nСрок действия: до {expiration_date}"
        )
    else:
        await update.message.reply_text("Ошибка при создании учетной записи. Пожалуйста, попробуйте позже.")

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
