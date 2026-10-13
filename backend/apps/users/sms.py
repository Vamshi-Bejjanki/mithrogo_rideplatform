import logging

logger = logging.getLogger(__name__)


class SmsProvider:
    def send(self, phone, message):
        raise NotImplementedError


class ConsoleSmsProvider(SmsProvider):
    """Development provider: writes the message to the log instead of sending an SMS."""

    def send(self, phone, message):
        logger.info("SMS to %s: %s", phone, message)
