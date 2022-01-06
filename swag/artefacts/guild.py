from attr import attrs, attrib
import arrow

from ..errors import InvalidTimeZone


def assert_timezone(self, attribute, timezone):
    try:
        arrow.now(timezone)
    except arrow.parser.ParserError:
        raise InvalidTimeZone(timezone)


@attrs(auto_attribs=True)
class Guild:
    timezone: str = attrib(validator=assert_timezone, default="UTC")


class GuildDict(dict):
    def __missing__(self, key):
        self[key] = Guild()
        return self[key]
