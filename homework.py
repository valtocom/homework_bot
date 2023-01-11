from exceptions import (VarNotFoundException,
                        MessageNotSentException,
                        EndpointHttpException,
                        StatusNotFound)

import os
import logging
import telegram
import time
import requests
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

VAR_NOT_FOUND = 'Отсутствие обязательных переменных окружения'
MESSAGE_IS_SENT = 'Удачная отправка сообщения в Telegram'
MESSAGE_NOT_SENT = 'Сбой при отправке сообщения в Telegram'
ENDPOINT_NOT_CONNECT = 'Недоступность эндпоинта'
ENDPOINT_ERROR = 'Сбои при запросе к эндпоинту'
KEYS_NOT_FOUND = 'Отсутствие ожидаемых ключей в ответе API'
STATUS_NOT_FOUND = 'Неожиданный статус домашней работы'
STATUS_NOT_CHANGED = 'Отсутствие в ответе новых статусов'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    tokens = [
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID
    ]
    return (all(tokens))


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception:
        logging.error(MESSAGE_NOT_SENT)
        raise MessageNotSentException(MESSAGE_NOT_SENT)
    else:
        logging.debug(MESSAGE_IS_SENT)


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    try:
        params = {'from_date': timestamp}
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception:
        logging.error(ENDPOINT_NOT_CONNECT)
        raise EndpointHttpException(ENDPOINT_NOT_CONNECT)

    response_status = response.status_code
    if response_status != HTTPStatus.OK:
        logging.error(ENDPOINT_ERROR)
        raise EndpointHttpException(ENDPOINT_ERROR)
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    try:
        list_works = response['homeworks']
    except KeyError as error:
        raise KeyError(f'Ошибка словаря по ключу homeworks: {error}')

    if not isinstance(response, dict):
        raise TypeError(f'Ответ API отличен от словаря: {TypeError}')

    if not isinstance(list_works, list):
        raise TypeError(f'Ответ API отличен от списка: {TypeError}')

    try:
        homework = list_works[0]
    except IndexError:
        raise IndexError(f'Список домашних работ пуст: {IndexError}')
    return homework


def parse_status(homework):
    """Извлекает из информации о домашней работе статус этой работы."""
    if 'homework_name' not in homework:
        logging.error(KEYS_NOT_FOUND)
        raise KeyError(KEYS_NOT_FOUND)
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_status not in HOMEWORK_VERDICTS:
        logging.error(STATUS_NOT_FOUND)
        raise StatusNotFound(STATUS_NOT_FOUND)
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical(VAR_NOT_FOUND)
        raise VarNotFoundException(VAR_NOT_FOUND)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(
        'main.log',
        maxBytes=50000000,
        backupCount=5
    )
    logger.addHandler(handler)

    while True:
        try:

            response = get_api_answer(timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)
            logging.debug(MESSAGE_IS_SENT)


if __name__ == '__main__':
    main()
