import datetime


class Event:
    def __init__(self, id, user):
        self.user = user
        self.id = id
        self.timestamp = datetime.datetime.now()

    def __lt__(self, other):
        return other.timestamp < self.timestamp  # newest first

    def __repr__(self):
        return f"(user={self.user}, id={self.id}, timestamp={self.timestamp})"