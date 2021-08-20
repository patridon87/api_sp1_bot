import os
import time
import requests
import telegram
from dotenv import load_dotenv
import logging
from http import HTTPStatus


logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('bot.log')
logger.addHandler(handler)

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
PRAKTIKUM_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'

bot = telegram.Bot(token=TELEGRAM_TOKEN)


class TGBotException(Exception):
    pass


def parse_homework_status(homework):
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']

        if homework_status == 'reviewing':
            return 'Работа взята на ревью'
        elif homework_status == 'rejected':
            verdict = 'К сожалению, в работе нашлись ошибки.'
        elif homework_status == 'approved':
            verdict = 'Ревьюеру всё понравилось, работа зачтена!'
        else:
            raise TGBotException('Неизвестный статус домашней работы')
        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'

    except KeyError:
        raise TGBotException('Сообщение не содержит обязательных полей')
        logger.error('Сообщение не содержит обязательных полей')


def get_homeworks(current_timestamp):
    url = PRAKTIKUM_URL
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    payload = {'from_date': current_timestamp}

    try:
        homework_statuses = requests.get(url, headers=headers, params=payload)
    except requests.RequestException:
        raise TGBotException('Сервис "Практикум.Домашка" недоступен')

    if homework_statuses.status_code == HTTPStatus.OK:
        return homework_statuses.json()
    else:
        raise TGBotException('Сетевая ошибка')


def send_message(message):
    return bot.send_message(chat_id=CHAT_ID, text=message)


def main():
    logger.debug('бот запущен')
    current_timestamp = int(time.time())  # Начальное значение timestamp
    while True:
        try:
            homework = get_homeworks(current_timestamp)
            if len(homework['homeworks']) != 0:
                current_timestamp = int(time.time())
                last_homework = homework['homeworks'][0]
                message = parse_homework_status(last_homework)
                send_message(message)
                logger.info('Сообщение отправлено')

            time.sleep(5 * 60)  # Опрашивать раз в пять минут

        except TGBotException as e:
            logger.error(f'Бот упал с ошибкой {e}')
            bot.send_message(chat_id=CHAT_ID, text=f'Бот упал с ошибкой {e}')
            time.sleep(5)

        except Exception as e:
            logger.error(f'Бот упал с ошибкой {e}')
            bot.send_message(chat_id=CHAT_ID, text=f'Бот упал с ошибкой {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
