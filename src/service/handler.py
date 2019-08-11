import json
import traceback

from aiohttp import web
from service.logger import applog
from service.simple_schema import RegisterEventSchema
from service.service import EventCounterService


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