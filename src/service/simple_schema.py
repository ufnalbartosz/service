class SchemaError(Exception):
    pass


class RegisterEventSchema:
    class Model:
        def __init__(self, event_id, user_id):
            self.event_id = event_id
            self.user_id = user_id

    def parse(self, request):
        return

    def load(self, payload):
        try:
            event_id = payload['eventId']
            user_id = payload['userId']
        except KeyError:
            raise SchemaError('missing register event values')
        return self.Model(event_id=event_id, user_id=user_id)


class ViewEventSchema:
    def __init__(self, interval_expectation):
        self.interval_expectation = interval_expectation

    class Model:
        def __init__(self, interval, event_id):
            self.interval = interval
            self.event_id = event_id

    def parse(self, request):
        try:
            interval = int(request.query.get('n'))
        except ValueError:
            raise SchemaError('wrong interval value')

        if interval > self.interval_expectation:
            raise SchemaError('wrong interval value')

        event_id = request.match_info['event_id']
        return self.Model(interval, event_id)

    def load(self, payload):
        return


class ViewEventsSchema:
    def __init__(self, interval_expectation):
        self.interval_expectation = interval_expectation

    class Model:
        def __init__(self, interval):
            self.interval = interval

    def parse(self, request):
        try:
            interval = int(request.query.get('n'))
        except ValueError:
            raise SchemaError('wrong interval value')

        if interval > self.interval_expectation:
            raise SchemaError('wrong interval value')

        return self.Model(interval)

    def load(self, payload):
        return
