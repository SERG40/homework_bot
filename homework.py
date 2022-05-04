import os
import logging
import sys
import json
import requests
import time

from http import HTTPStatus
from telegram import Bot
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s, %(levelname)s, %(message)s',
    handlers=[logging.FileHandler('log.txt'),
              logging.StreamHandler(sys.stdout)])

load_dotenv()
logger = logging.getLogger('logger')


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляем сообщение в ТГ."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Бот отправил сообщение {message}')
    except Exception:
        logger.error(
            f'Сбой при отправке в Телеграмм сообщения "{message}"',
            exc_info=True
        )
        return False
    return True


def get_api_answer(current_timestamp):
    """Получаем API."""
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(ENDPOINT, headers=HEADERS,
                                         params=params)
        if homework_statuses.status_code != HTTPStatus.OK:
            logger.error(f'Ошибка API {homework_statuses.status_code}')
            raise ConnectionError('Ошибка соединения')
    except requests.exceptions.RequestException as error:
        logger.error(f'Сервер Яндекс.Практикум вернул ошибку: {error}.')
        send_message(f'Сервер Яндекс.Практикум вернул ошибку: {error}.')
    try:
        return homework_statuses.json()
    except json.JSONDecodeError:
        logger.error('Сервер вернул невалидный json.')
        send_message('Сервер вернул невалидный json.')


def check_response(response):
    """Проверяем response."""
    if type(response) is not dict:
        raise TypeError('Ошибка типа')
    try:
        homeworks_list = response.get('homeworks')
    except KeyError:
        logger.error('Неверный ключ')
        raise KeyError('Неверный ключ')
    try:
        homeworks_list[0]
    except IndexError:
        logger.error('Нет домашней работы')
        raise IndexError('Нет домашней работы')
    return homeworks_list


def parse_status(homework):
    """Проверяем статус."""
    pprint(homework)
    if isinstance(homework, dict):
        homework_name = homework.get('homework_name')
        homework_status = homework.get('status')

        if homework_status not in HOMEWORK_STATUSES:
            logger.error('Недокументированный статус')
            raise KeyError('Отстутствует ключ')
        else:
            verdict = HOMEWORK_STATUSES.get(homework_status)
            if homework_name is not None:
                return (f'Изменился статус проверки работы "{homework_name}".'
                        f'{verdict}')
    else:
        logger.error('Ошибка')
        return f'Ошибка типа! Проверь {homework}'


def check_tokens():
    """Проверяет доступность токенов."""
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        return True
    else:
        if PRACTICUM_TOKEN is None:
            logger.critical('отсутствует : PRACTICUM_TOKEN')
        if TELEGRAM_TOKEN is None:
            logger.critical('отсутствует : TELEGRAM_TOKEN')
        if TELEGRAM_CHAT_ID is None:
            logger.critical('отсутствует : TELEGRAM_CHAT_ID')
    return False


def main():
    """Основная логика работы бота."""
    current_timestamp = 0
    bot = Bot(token=TELEGRAM_TOKEN)
    if check_tokens() is not True:
        raise ValueError('Беда с токенами.')
    while True:
        try:
            all_homework = get_api_answer(current_timestamp)
            if len(all_homework['homeworks']) > 0:
                homework = all_homework['homeworks'][0]
                send_message(bot, parse_status(homework))
                logger.info('Сообщение отправлено')
            time.sleep(RETRY_TIME)
        except Exception as error:
            logger.error(f'Сбой в работе программы: {error}')
            send_message(f'Сбой в работе программы: {error}')
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
