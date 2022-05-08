from __future__ import annotations

from typing import TYPE_CHECKING, Union

from disnake import User

from swag.id import CagnotteId, UserId

if TYPE_CHECKING:
    from ..blockchain import SwagChain

from attr import attrs, attrib

from ..artefacts import CagnotteAccount

from ..block import Block

from ..errors import (
    AlreadyCagnotteManager,
    CagnotteDestructionForbidden,
    CagnotteNameAlreadyExist,
    NotCagnotteManager,
    OrphanCagnotte,
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
    user_id = attrib(type=UserId, converter=UserId)

    @user_id.default
    def _user_id_default(self):
        return self.issuer_id

    def validate(self, db: SwagChain):
        cagnotte_names = (cagnotte.name for cagnotte in db._accounts.cagnottes.values())
        if self.new_name in cagnotte_names:
            raise CagnotteNameAlreadyExist

    def execute(self, db: SwagChain):
        cagnotte = db._accounts[self.cagnotte_id]

        if self.user_id not in cagnotte.managers:
            raise NotCagnotteManager(self.user_id)

        cagnotte.name = self.new_name


@attrs(frozen=True, kw_only=True)
class CagnotteParticipantsReset(Block):
    cagnotte_id = attrib(type=CagnotteId, converter=CagnotteId)
    user_id = attrib(type=UserId, converter=UserId)

    @user_id.default
    def _user_id_default(self):
        return self.issuer_id

    def execute(self, db: SwagChain):
        cagnotte = db._accounts[self.cagnotte_id]

        if self.user_id not in cagnotte.managers:
            raise NotCagnotteManager(self.user_id)

        cagnotte.participants.clear()


@attrs(frozen=True, kw_only=True)
class CagnotteDeletion(Block):
    cagnotte_id = attrib(type=CagnotteId, converter=CagnotteId)
    user_id = attrib(type=UserId, converter=UserId)

    @user_id.default
    def _user_id_default(self):
        return self.issuer_id

    def execute(self, db: SwagChain):
        cagnotte = db._accounts[self.cagnotte_id]

        if self.user_id not in cagnotte.managers:
            raise NotCagnotteManager(self.user_id)

        if not cagnotte.is_empty:
            raise CagnotteDestructionForbidden

        del db._accounts[self.cagnotte_id]


@attrs(frozen=True, kw_only=True)
class CagnotteAddManagerBlock(Block):
    cagnotte_id = attrib(type=CagnotteId, converter=CagnotteId)
    new_manager = attrib(type=UserId, converter=UserId)
    user_id = attrib(type=UserId, converter=UserId)

    @user_id.default
    def _user_id_default(self):
        return self.issuer_id

    def execute(self, db: SwagChain):
        cagnotte = db._accounts[self.cagnotte_id]

        if self.user_id not in cagnotte.managers:
            raise NotCagnotteManager(self.user_id)

        if self.new_manager in cagnotte.managers:
            raise AlreadyCagnotteManager(self.new_manager)

        db._accounts[self.cagnotte_id].managers.append(self.new_manager)


@attrs(frozen=True, kw_only=True)
class CagnotteRevokeManagerBlock(Block):
    cagnotte_id = attrib(type=CagnotteId, converter=CagnotteId)
    manager_id = attrib(type=UserId, converter=UserId)
    user_id = attrib(type=UserId, converter=UserId)

    @user_id.default
    def _user_id_default(self):
        return self.issuer_id

    def execute(self, db: SwagChain):
        cagnotte = db._accounts[self.cagnotte_id]

        if self.user_id not in cagnotte.managers:
            raise NotCagnotteManager(self.user_id)

        if self.manager_id not in cagnotte.managers:
            raise NotCagnotteManager(self.manager_id)

        if len(cagnotte.managers) <= 1:
            raise OrphanCagnotte

        db._accounts[self.cagnotte_id].managers.remove(self.manager_id)
