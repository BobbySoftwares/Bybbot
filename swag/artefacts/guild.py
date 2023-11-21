from typing import Optional
from attr import attrs, attrib

from swag.assert_timezone import assert_timezone


@attrs(auto_attribs=True)
class Guild:
    timezone: str = attrib(validator=assert_timezone, default="UTC")
    system_channel_id: Optional[int] = None
    forbes_channel_id: Optional[int] = None


class GuildDict(dict):
    def __missing__(self, key):
        self[key] = Guild()
        return self[key]
