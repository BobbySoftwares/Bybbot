import re
from attr import attrib, attrs

from .errors import InvalidCagnotteId


def user_id_converter(user_id):
    if type(user_id) is UserId:
        return user_id.id
    else:
        return int(user_id)


@attrs(frozen=True, auto_attribs=True)
class UserId:
    id: int = attrib(converter=user_id_converter)

    def __str__(self) -> str:
        return f"<@{self.id}>"


cagnotte_id_regex = re.compile("^€\w*$", re.A)


def cagnotte_id_converter(cagnotte_id):
    if type(cagnotte_id) is CagnotteId:
        return cagnotte_id.id
    else:
        return str(cagnotte_id)


@attrs(frozen=True, auto_attribs=True)
class CagnotteId:
    id: str = attrib(converter=cagnotte_id_converter)

    @id.validator
    def _validate(self, attribute, value):
        if not re.match(cagnotte_id_regex, value):
            raise InvalidCagnotteId

    def __str__(self) -> str:
        return self.id
