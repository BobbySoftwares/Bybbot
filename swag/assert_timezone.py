from arrow import Arrow
import arrow


def assert_timezone(self, attribute, timezone):
    try:
        arrow.now(timezone)
    except arrow.parser.ParserError:
        raise InvalidTimeZone(timezone)
