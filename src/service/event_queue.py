import asyncio
import datetime


class EventQueue(asyncio.PriorityQueue):
    def __init__(self, event_expiration_time: int, **kwargs):
        super().__init__(**kwargs)
        self.event_expiration_time = event_expiration_time
        self.mutex = asyncio.Lock()

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
        async with self.mutex:
            for event in self:
                if event.timestamp > expiration_threshold:
                    await actual_events.put(event)
                else:
                    break
        return actual_events