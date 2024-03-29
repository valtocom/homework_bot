class MessageNotSentException(Exception):
    """Сбой при отправке сообщения в Telegram."""
    pass


class EndpointHttpException(Exception):
    """Сбои при запросе к эндпоинту"""
    pass


class StatusNotFound(Exception):
    """Неожиданный статус домашней работы, обнаруженный в ответе API"""
    pass
