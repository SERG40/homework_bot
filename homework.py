import os
import requests
import time

from telegram import Bot
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
bot = Bot(token=TELEGRAM_TOKEN)

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    return bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    return homework_statuses.json()


def check_response(response):
    


# def parse_status(homework):
#     homework_name = ...
#     homework_status = ...

#     ...

#     verdict = ...

#     ...

#     return f'Изменился статус проверки работы "{homework_name}". {verdict}'


# def check_tokens():
#     ...


def main():
    """Основная логика работы бота."""
    print(get_api_answer(0))
    check_response(get_api_answer)
    print(check_response(get_api_answer(0)))
#     ...

#     bot = telegram.Bot(token=TELEGRAM_TOKEN)
#     current_timestamp = int(time.time())

#     ...

#     while True:
#         try:
#             response = ...

#             ...

#             current_timestamp = ...
#             time.sleep(RETRY_TIME)

#         except Exception as error:
#             message = f'Сбой в работе программы: {error}'
#             ...
#             time.sleep(RETRY_TIME)
#         else:
#             ...


if __name__ == '__main__':
    main()
