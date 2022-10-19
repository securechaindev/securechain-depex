from json import JSONEncoder

from bson import ObjectId


class JSONencoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return JSONEncoder.default(self, o)