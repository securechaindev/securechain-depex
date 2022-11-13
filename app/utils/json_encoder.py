from json import JSONEncoder

from bson import ObjectId

from datetime import datetime


class JSONencoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return str(o)
        return JSONEncoder.default(self, o)