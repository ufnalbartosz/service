import json
import traceback

from aiohttp import web
from service.logger import applog
from service.simple_schema import RegisterEventSchema, ViewEventSchema, ViewEventsSchema, SchemaError
from service.service import EventCounterService


class ServiceHandler:
    def __init__(self, service: EventCounterService):
        self.service = service
        self.register_event_schema = RegisterEventSchema()
        self.view_event_schema = ViewEventSchema(self.service.event_expiration_time)
        self.view_events_schema = ViewEventsSchema(self.service.event_expiration_time)

    async def register_event(self, request: web.Request) -> web.Response:
        try:
            payload = await request.json()
        except json.decoder.JSONDecodeError as exc:
            applog.debug(f'error happened: {type(exc)}')
            traceback.print_exc()
            return web.Response(status=400, text='wrong body format')

        try:
            result = self.register_event_schema.load(payload)
        except SchemaError as exc:
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
        try:
            result = self.view_event_schema.parse(request)
        except SchemaError as exc:
            applog.debug(f'error happened: {type(exc)}')
            traceback.print_exc()
            return web.Response(status=400, text='wrong query parameters')

        event_views = await self.service.get_unique_users_count(result.event_id, result.interval)
        payload = {"eventId": result.event_id, "views": event_views}
        return web.Response(status=200, body=json.dumps(payload))

    async def view_events(self, request: web.Request) -> web.Response:
        try:
            result = self.view_events_schema.parse(request)
        except SchemaError as exc:
            applog.debug(f'error happened: {type(exc)}')
            traceback.print_exc()
            return web.Response(status=400, text='wrong query parameters')

        events_views = await self.service.get_all_users_count(result.interval)
        return web.Response(status=200, body=json.dumps(events_views))

    async def start_background_tasks(self, app):
        applog.info('starting background task')
        app['bg-task'] = app.loop.create_task(self.service.background_task())

    async def cleanup_background_tasks(self, app):
        applog.info('cleaning up background task')
        self.service.background_task_running = False
        app['bg-task'].cancel()
        await app['bg-task']
