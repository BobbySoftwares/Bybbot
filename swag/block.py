from __future__ import annotations

from typing import TYPE_CHECKING

from swag.id import UserId

if TYPE_CHECKING:
    from blockchain import SwagChain

from attr import attrs, attrib
import arrow
from arrow import Arrow, utcnow


@attrs(frozen=True, kw_only=True)
class Block:
    timestamp = attrib(type=Arrow, converter=arrow.get, factory=utcnow)
    issuer_id = attrib(type=UserId, converter=UserId)

    def validate(self, db: SwagChain):
        pass

    def execute(self, db: SwagChain):
        raise NotImplementedError
