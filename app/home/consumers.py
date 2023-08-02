import logging
from channels.generic.websocket import AsyncWebsocketConsumer

log = logging.getLogger('app')


class HomeConsumer(AsyncWebsocketConsumer):
    async def websocket_connect(self, event):
        log.debug(event)
        await self.channel_layer.group_add('home', self.channel_name)
        await self.accept()

    async def websocket_send(self, event):
        log.debug(event)
        if self.scope['client'][1] is None:
            return log.debug('client 1 is None')
        await self.send(text_data=event['text'])
