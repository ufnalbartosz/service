import json
import datetime
import asyncio
from marshmallow import Schema, fields

from typing import Mapping
from aiohttp import web


class Event:
    def __init__(self, id, user):
        self.user = user
        self.id = id
        self.timestamp = datetime.datetime.now()

    def __cmp__(self, other):
        return self.timestamp < other.timestamp


class EventCounterService:
    expiration_time = 60

    def __init__(self):
        self.events = asyncio.PriorityQueue()

    async def register(self, event_id: str, user_id: str) -> bool:
        try:
            await self.events.put(Event(event_id, user_id))

        except Exception:
            return False

        else:
            return True

    def dump_expired(self):
        now = datetime.datetime.now()
        delta = datetime.timedelta(minutes=self.expiration_time)

    async def get_unique_users_count(self, event_id: str, interval: int) -> int:
        return int()

    async def get_all_users_count(self, interval: int) -> Mapping[str, int]:
        return {'eventId': 1}


class EventData:
    def __init__(self, event_id, user_id):
        self.event_id = event_id
        self.user_id = user_id


class RegisterEventSchema:
    def load(self, payload):
        event_id = payload['eventId']
        user_id = payload['userId']
        return EventData(event_id=event_id, user_id=user_id)


class ServiceHandler:
    def __init__(self, service: EventCounterService):
        self.service = service
        self.register_event_schema = RegisterEventSchema()

    async def register_event(self, request: web.Request) -> web.Response:
        # body: `{"eventId": "e1", "userId": "b16e6dc4-1672-4068-ad2f-54be1c39e18c"}`
        try:
            payload = await request.json()
        except json.decoder.JSONDecodeError:
            return web.Response(status=400)
        try:
            result = self.register_event_schema.load(payload)
        except KeyError:
            return web.Response(status=400)

        register_status = await self.service.register(result.event_id, result.user_id)

        if register_status:
            return web.Response(status=200)
        else:
            return web.Response(status=400)

    async def get_event(self, request: web.Request) -> web.Response:
        # response: `{"eventId":"e1", "views":1}`
        return web.Response()

    async def get_all_events(self, request: web.Request) -> web.Response:
        # response `[{"eventId":"e1", "views":1}, {"eventId":"e2", "views":5}]`
        return web.Response()


def spawn_app():
    service = EventCounterService()
    handler = ServiceHandler(service)

    app = web.Application()
    app.add_routes([
        web.post('/register/event', handler.register_event),
        web.get('/views/{eventId}?n={N}', handler.get_event),
        web.get('/views/all?n={N}', handler.get_all_events),

    ])
    return app


def main():
    web.run_app(spawn_app())


if __name__ == '__main__':
    main()
