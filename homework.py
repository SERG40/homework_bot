import os
import logging
import sys
import json
import requests
import time

from telegram import Bot
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s, %(levelname)s, %(message)s',
    handlers=[logging.FileHandler('log.txt'),
              logging.StreamHandler(sys.stdout)])

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
    """Отправляем сообщение в ТГ."""
    return bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    """Получаем API."""
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(ENDPOINT, headers=HEADERS,
                                         params=params)
    except requests.exceptions.RequestException as error:
        logging.error(f'Сервер Яндекс.Практикум вернул ошибку: {error}.')
        send_message(f'Сервер Яндекс.Практикум вернул ошибку: {error}.')
    try:
        return homework_statuses.json()
    except json.JSONDecodeError:
        logging.error('Сервер вернул невалидный json.')
        send_message('Сервер вернул невалидный json.')


def check_response(response):
    """Проверяем response."""
    homeworks = response['homeworks']
    if homeworks is None:
        raise KeyError('Не содержит ключ или пустое значение.')
    if not homeworks:
        return False
    homeworks_status = response['homeworks'][0].get('status')
    if homeworks_status in HOMEWORK_STATUSES:
        return homeworks
    else:
        raise KeyError('Отсутствие или неверный статус работы.')


def parse_status(homework):
    """Проверяем статус."""
    try:
        homework_name = homework['homework_name']
    except KeyError:
        logging.error('Неверный ответ сервера')

    homework_status = homework.get('status')
    verdict = ''
    if ((homework_status is None) or (
        homework_status == '')) or ((
            homework_status != 'approved') and (
            homework_status != 'rejected')):
        logging.error(f'Статус работы некорректен: {homework_status}')
    if homework_status == 'rejected':
        verdict = 'Работа проверена: у ревьюера есть замечания.'
    elif homework_status == 'approved':
        verdict = 'Работа проверена: ревьюеру всё понравилось. Ура!'
    elif homework_status == 'reviewing':
        verdict = 'Работа взята на проверку ревьюером.'
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов."""
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        logging.critical('Отсутствие ID или Токена')
        return True
    return False


def main():
    """Основная логика работы бота."""
    current_timestamp = int(time.time())
    while True:
        try:
            all_homework = get_api_answer(current_timestamp)
            if len(all_homework['homeworks']) > 0:
                homework = all_homework['homeworks'][0]
                send_message(bot, parse_status(homework))
                logging.info('Сообщение отправлено')
            time.sleep(RETRY_TIME)

        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
            send_message(f'Сбой в работе программы: {error}')
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
