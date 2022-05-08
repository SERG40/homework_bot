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
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logger.info(f'Бот отправил сообщение {message}')


def get_api_answer(current_timestamp):
    """Получаем API."""
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(ENDPOINT, headers=HEADERS,
                                         params=params)
    except ConnectionError as error:
        logger.error(f'Нет соединения{error}')
        raise ConnectionError(f'Нет соединения{error}')
    try:
        if homework_statuses.status_code != HTTPStatus.OK:
            logger.error(f'Ошибка API {homework_statuses.status_code}')
            raise ConnectionError('Ошибка соединения')
    except requests.exceptions.RequestException as error:
        logger.error(f'Сервер Яндекс.Практикум вернул ошибку: {error}.')
        raise RuntimeError('Сервер Яндекс.Практикум вернул ошибку')
    try:
        return homework_statuses.json()
    except json.JSONDecodeError:
        raise requests.JSONDecodeError('Сервер вернул невалидный json.')


def check_response(response):
    """Проверяем response."""
    if not isinstance(response, dict):
        raise TypeError('Ошибка типа указанного класса нужен словарь')
    homeworks = response.get('homeworks')
    if homeworks is None:
        logger.error('API не содержит ключ')
        raise Exception('API не содержит ключ')
    if type(homeworks) is not list:
        raise TypeError('Ошибка типа передается не список')
    return homeworks


def parse_status(homework):
    """Проверяем статус."""
    if isinstance(homework, dict):
        homework_name = homework.get('homework_name')
        homework_status = homework.get('status')
        if homework_name is None:
            logger.error('Отсутствует ключ homework_name')
            raise KeyError('Отсутствует ключ homework_name')
        elif homework_status not in HOMEWORK_STATUSES:
            logger.error('Недокументированный статус')
            raise KeyError('Отстутствует ключ')
        else:
            verdict = HOMEWORK_STATUSES.get(homework_status)
            if verdict is not None:
                return (f'Изменился статус проверки работы "{homework_name}".'
                        f'{verdict}')
            else:
                logger.error(f'Статус работы некорректен: {homework_status}')
                raise Exception(
                    f'Статус работы некорректен: {homework_status}')
    else:
        logger.error('Ошибка типа!')
        raise TypeError(f'Ошибка типа! Проверь {homework}')


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
    current_timestamp = int(time.time()) - RETRY_TIME
    bot = Bot(token=TELEGRAM_TOKEN)
    new_error = ''
    if check_tokens() is not True:
        raise ValueError('Беда с токенами.')
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            current_timestamp = response.get('current_date', current_timestamp)
            if len(homeworks) > 0:
                send_message(bot, parse_status(response['homeworks']))
                logger.info('Сообщение отправлено')
        except Exception as error:
            error_message = f'Сбой в работе программы: {error}'
            logger.error(error_message, exc_info=True)
            if error_message != new_error:
                send_message(bot, error_message)
            else:
                new_error = error_message
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
