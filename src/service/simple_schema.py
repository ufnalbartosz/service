class RegisterEventSchema:
    def load(self, payload):
        event_id = payload['eventId']
        user_id = payload['userId']
        return EventData(event_id=event_id, user_id=user_id)


class EventData:
    def __init__(self, event_id, user_id):
        self.event_id = event_id
        self.user_id = user_id