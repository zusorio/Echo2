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
                # TODO: Instead of truncating, splitting into several messages would be much smarter ¯\_(ツ)_/¯
                self._webhook.send(content=f"```{msg[0:1980]}```", wait=True, username=self._username, avatar_url="https://cdn.discordapp.com/app-icons/581523092363411493/9f85d39eb6321ad12b2d13396c4595f5.png?size=512")

        except Exception:
            self.handleError(record)
