import logging
from discord import Webhook, RequestsWebhookAdapter


class DiscordHandler(logging.Handler):
    """
    A handler class which writes logging records, appropriately formatted,
    to a Discord Server using webhooks.
    """

    def __init__(self, webhook_url, username):
        logging.Handler.__init__(self)

        if webhook_url is None or webhook_url == "":
            raise ValueError("webhook_url parameter must be given and can not be empty!")

        if username is None or username == "":
            raise ValueError("agent parameter must be given and can not be empty!")

        self._url = webhook_url
        self._webhook = Webhook.from_url(self._url, adapter=RequestsWebhookAdapter())
        self._username = username

    def emit(self, record):
        try:
            msg = self.format(record)
            if msg:
                self._webhook.send(content=f"```{msg}```", wait=True, username=self._username)

        except Exception:
            self.handleError(record)
