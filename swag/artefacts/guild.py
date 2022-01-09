from attr import attrs, attrib

from swag.utils import assert_timezone


@attrs(auto_attribs=True)
class Guild:
    timezone: str = attrib(validator=assert_timezone, default="UTC")


class GuildDict(dict):
    def __missing__(self, key):
        self[key] = Guild()
        return self[key]
