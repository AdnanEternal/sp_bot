import asyncio
from splusthon import events

def register_handlers(client):
    @client.on(events.NewMessage(incoming=True))
    async def central_router(event):
        pass