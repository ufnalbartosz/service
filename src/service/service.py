import asyncio
import collections
import traceback
import typing

from service.logger import applog
from service.event import Event
from service.event_queue import EventQueue


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

    async def get_all_users_count(self, interval: int) -> typing.Mapping[str, int]:
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