from aiohttp import web
from service.handler import ServiceHandler
from service.service import EventCounterService


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
