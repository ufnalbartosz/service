import json
import datetime
import asyncio
import traceback
import collections
from .logger import applog
from aiohttp import web
from typing import Mapping

from marshmallow import Schema, fields


class Event:
    def __init__(self, id, user):
        self.user = user
        self.id = id
        self.timestamp = datetime.datetime.now()

    def __lt__(self, other):
        return other.timestamp < self.timestamp  # newest first

    def __repr__(self):
        return f"(user={self.user}, id={self.id}, timestamp={self.timestamp})"


class EventQueue(asyncio.PriorityQueue):
    def __init__(self, event_expiration_time: int, **kwargs):
        super().__init__(**kwargs)
        self.event_expiration_time = event_expiration_time

    def get_events_within_interval(self, interval: int):
        timespan_beginning = datetime.datetime.now() - datetime.timedelta(minutes=interval)
        for event in self:
            if timespan_beginning < event.timestamp:
                yield event
            else:
                break

    def __iter__(self):
        q = self._queue

        if not q:
            return

        next_indices = [0]
        while next_indices:
            min_index = min(next_indices, key=q.__getitem__)
            yield q[min_index]
            next_indices.remove(min_index)
            if 2 * min_index + 1 < len(q):
                next_indices.append(2 * min_index + 1)
            if 2 * min_index + 2 < len(q):
                next_indices.append(2 * min_index + 2)

    async def get_actual_events(self):
        now = datetime.datetime.now()
        delta = datetime.timedelta(minutes=self.event_expiration_time)
        expiration_threshold = now - delta
        actual_events = EventQueue(self.event_expiration_time)
        for event in self:
            if event.timestamp > expiration_threshold:
                await actual_events.put(event)
            else:
                break
        return actual_events


class EventCounterService:
    event_expiration_time = 1  # minutes
    background_task_interval = 20  # seconds

    def __init__(self):
        self.events = EventQueue(self.event_expiration_time)
        self.background_task_running = True

    async def register(self, event_id: str, user_id: str) -> bool:
        try:
            await self.events.put(Event(event_id, user_id))
            applog.debug(list(self.events.get_events_within_interval(1)))  # FIXME remove debug
        except Exception as exc:
            applog.debug(f'error happened: {type(exc)}')
            traceback.print_exc()
            return False
        else:
            return True

    async def get_unique_users_count(self, event_id: str, interval: int) -> int:
        user_ids = set()
        for event in self.events.get_events_within_interval(interval):
            if event.id == event_id:
                user_ids.add(event.user)
        return len(user_ids)

    async def get_all_users_count(self, interval: int) -> Mapping[str, int]:
        events_views = collections.defaultdict(set)
        for event in self.events.get_events_within_interval(interval):
            events_views[event.id].add(event.user)
        return {event_id: len(user_ids) for event_id, user_ids in events_views.items()}

    async def background_task(self):
        while self.background_task_running:
            events = await self.events.get_actual_events()
            # NOTE: not ideal but left for future debug
            applog.debug(f'expired events: {set(self.events._queue) - set(events._queue)}')
            self.events = events
            await asyncio.sleep(self.background_task_interval)


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
        try:
            payload = await request.json()
        except json.decoder.JSONDecodeError as exc:
            applog.debug(f'error happened: {type(exc)}')
            traceback.print_exc()
            return web.Response(status=400, text='wrong body format')

        try:
            result = self.register_event_schema.load(payload)
        except KeyError as exc:
            applog.debug(f'error happened: {type(exc)}')
            traceback.print_exc()
            return web.Response(status=400, text='missing register event values')

        register_status = await self.service.register(result.event_id, result.user_id)

        if register_status:
            return web.Response(status=200)
        else:
            applog.info(f'bad register status: {register_status}')
            return web.Response(status=400)

    async def view_event(self, request: web.Request) -> web.Response:
        event_id = request.match_info['event_id']  # TODO add validation
        interval = int(request.query.get('n'))  # TODO add validation

        event_views = await self.service.get_unique_users_count(event_id, interval)
        payload = {"eventId": event_id, "views": event_views}  # TODO use response body builder
        return web.Response(status=200, body=json.dumps(payload))

    async def view_events(self, request: web.Request) -> web.Response:
        # response `[{"eventId":"e1", "views":1}, {"eventId":"e2", "views":5}]`
        interval = int(request.query.get('n'))  # TODO add validation
        # token = request.headers.get('Token')
        events_views = await self.service.get_all_users_count(interval)
        return web.Response(status=200, body=json.dumps(events_views))

    async def start_background_tasks(self, app):
        applog.info('starting background task')
        app['dispatch'] = app.loop.create_task(self.service.background_task())

    async def cleanup_background_tasks(self, app):
        applog.info('cleaning up background task')
        self.service.background_task_running = False
        app['dispatch'].cancel()
        await app['dispatch']


def spawn_app():
    service = EventCounterService()
    handler = ServiceHandler(service)

    app = web.Application()
    app.add_routes([
        web.post('/register/event', handler.register_event),
        web.get('/views/{event_id}', handler.view_event),
        web.get('/debug/views', handler.view_events),

    ])
    app.on_startup.append(handler.start_background_tasks)
    app.on_cleanup.append(handler.cleanup_background_tasks)
    return app


def main():
    web.run_app(spawn_app())


if __name__ == '__main__':
    main()
