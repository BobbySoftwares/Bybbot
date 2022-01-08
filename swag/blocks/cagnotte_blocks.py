from __future__ import annotations

from typing import TYPE_CHECKING, Union

from swag.id import CagnotteId, UserId

if TYPE_CHECKING:
    from ..blockchain import SwagChain

from attr import attrs, attrib

from ..artefacts import CagnotteAccount

from ..block import Block

from ..errors import (
    CagnotteDestructionForbidden,
    CagnotteNameAlreadyExist,
    NotCagnotteManager,
)

from ..currencies import Swag, Style


@attrs(frozen=True, kw_only=True)
class CagnotteCreation(Block):
    cagnotte_id = attrib(type=CagnotteId, converter=CagnotteId)
    name = attrib(type=str)
    creator = attrib(type=UserId, converter=UserId)

    def validate(self, db: SwagChain):
        cagnotte_names = (cagnotte.name for cagnotte in db._accounts.cagnottes.values())
        if self.cagnotte_id in db._accounts.cagnottes or self.name in cagnotte_names:
            raise CagnotteNameAlreadyExist

    def execute(self, db: SwagChain):
        db._accounts[self.cagnotte_id] = CagnotteAccount(self.name, [self.creator])


@attrs(frozen=True, kw_only=True)
class CagnotteRenaming(Block):
    cagnotte_id = attrib(type=CagnotteId, converter=CagnotteId)
    new_name = attrib(type=str)

    def validate(self, db: SwagChain):
        cagnotte_names = (cagnotte.name for cagnotte in db._accounts.cagnottes.values())
        if self.name in cagnotte_names:
            raise CagnotteNameAlreadyExist

    def execute(self, db: SwagChain):
        cagnotte = db._accounts[self.cagnotte_id]

        if self.issuer_id not in cagnotte.managers:
            raise NotCagnotteManager

        cagnotte.name = self.new_name


@attrs(frozen=True, kw_only=True)
class CagnotteParticipantsReset(Block):
    cagnotte_id = attrib(type=CagnotteId, converter=CagnotteId)

    def execute(self, db: SwagChain):
        cagnotte = db._accounts[self.cagnotte_id]

        if self.issuer_id not in cagnotte.managers:
            raise NotCagnotteManager

        cagnotte.participants.clear()


@attrs(frozen=True, kw_only=True)
class CagnotteDeletion(Block):
    cagnotte_id = attrib(type=CagnotteId, converter=CagnotteId)

    def execute(self, db: SwagChain):
        cagnotte = db._accounts[self.cagnotte_id]
        print(cagnotte)

        if self.issuer_id not in cagnotte.managers:
            raise NotCagnotteManager

        if not cagnotte.is_empty:
            raise CagnotteDestructionForbidden

        del db._accounts[self.cagnotte_id]
