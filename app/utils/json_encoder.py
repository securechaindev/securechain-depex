from json import JSONEncoder, loads

from typing import Any

from datetime import datetime

from bson import ObjectId


class JSONencoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return str(o)
        return JSONEncoder.default(self, o)


def json_encoder(raw_response: dict[str, Any]) -> Any:
    return loads(JSONencoder().encode(raw_response))