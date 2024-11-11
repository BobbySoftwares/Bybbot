from __future__ import annotations

from typing import TYPE_CHECKING, Union

from disnake import User

from swag.artefacts.accounts import CagnotteRank
from swag.artefacts.services import Service
from swag.id import AccountId, CagnotteId, UserId, get_id_from_str

if TYPE_CHECKING:
    from ..blockchain import SwagChain

from attr import attrs, attrib

from ..artefacts import CagnotteAccount

from ..block import Block

from ..errors import (
    AlreadyCagnotteManager,
    BadRankService,
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

        if self.issuer_id not in cagnotte.managers:
            raise NotCagnotteManager(self.issuer_id)

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

        if self.issuer_id not in cagnotte.managers:
            raise NotCagnotteManager(self.issuer_id)

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

        if self.issuer_id not in cagnotte.managers:
            raise NotCagnotteManager(self.issuer_id)

        if not cagnotte.is_empty:
            raise CagnotteDestructionForbidden

        del db._accounts[self.cagnotte_id]


@attrs(frozen=True, kw_only=True)
class CagnotteAddManagerBlock(Block):
    cagnotte_id = attrib(type=CagnotteId, converter=CagnotteId)
    new_manager = attrib(type=UserId, converter=UserId)

    def execute(self, db: SwagChain):
        cagnotte = db._accounts[self.cagnotte_id]

        if self.issuer_id not in cagnotte.managers:
            -(self.issuer_id)

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

        if self.issuer_id not in cagnotte.managers:
            raise NotCagnotteManager(self.issuer_id)

        if self.manager_id not in cagnotte.managers:
            raise NotCagnotteManager(self.manager_id)

        if len(cagnotte.managers) <= 1:
            raise OrphanCagnotte

        db._accounts[self.cagnotte_id].managers.remove(self.manager_id)


@attrs(frozen=True, kw_only=True)
class CagnotteAddRankBlock(Block):
    cagnotte_id = attrib(type=CagnotteId, converter=CagnotteId)
    user_id = attrib(type=UserId, converter=UserId)
    rank = attrib(type=CagnotteRank)

    def execute(self, db: SwagChain):
        cagnotte = db._accounts[self.cagnotte_id]

        if self.user_id not in cagnotte.managers:
            raise NotCagnotteManager(self.user_id)

        cagnotte.accounts_ranking[self.rank.name] = self.rank


@attrs(frozen=True, kw_only=True)
class CagnotteAddAccountToRankBlock(Block):
    cagnotte_id = attrib(type=CagnotteId, converter=CagnotteId)
    user_id = attrib(type=UserId, converter=UserId)
    rank_name = attrib(type=str)
    account_to_add = attrib(type=AccountId)

    def execute(self, db: SwagChain):
        cagnotte = db._accounts[self.cagnotte_id]

        if self.user_id not in cagnotte.managers:
            raise NotCagnotteManager(self.user_id)

        cagnotte.accounts_ranking[self.rank_name].members.append(self.account_to_add)


@attrs(frozen=True, kw_only=True)
class CagnotteRemoveAccountToRankBlock(Block):
    cagnotte_id = attrib(type=CagnotteId, converter=CagnotteId)
    user_id = attrib(type=UserId, converter=UserId)
    rank_name = attrib(type=str)
    account_to_remove = attrib(type=AccountId)

    def execute(self, db: SwagChain):
        cagnotte = db._accounts[self.cagnotte_id]

        if self.user_id not in cagnotte.managers:
            raise NotCagnotteManager(self.user_id)

        cagnotte.accounts_ranking[self.rank_name].members.remove(self.account_to_remove)


@attrs(frozen=True, kw_only=True)
class CagnotteRemoveRankBlock(Block):
    cagnotte_id = attrib(type=CagnotteId, converter=CagnotteId)
    user_id = attrib(type=UserId, converter=UserId)
    rank_name = attrib(type=str)

    def execute(self, db: SwagChain):
        cagnotte = db._accounts[self.cagnotte_id]

        if self.user_id not in cagnotte.managers:
            raise NotCagnotteManager(self.user_id)

        cagnotte.accounts_ranking.pop(self.rank_name)

        for service in cagnotte.services:
            if service.authorized_rank is not None:
                service.authorized_rank.remove(self.rank_name)


@attrs(frozen=True, kw_only=True)
class ServiceCreation(Block):
    user_id = attrib(type=UserId, converter=UserId)
    cagnotte_id = attrib(type=CagnotteId, converter=CagnotteId)
    service = attrib(type=Service)

    def execute(self, db: SwagChain):

        cagnotte = db._accounts[self.cagnotte_id]

        if self.issuer_id not in cagnotte.managers:
            raise NotCagnotteManager(self.issuer_id)

        cagnotte.services.append(self.service)


@attrs(frozen=True, kw_only=True)
class UseService(Block):
    user_id = attrib(type=UserId, converter=UserId)
    cagnotte_id = attrib(type=CagnotteId, converter=CagnotteId)
    service_id = attrib(type=int)

    def execute(self, db: SwagChain):
        cagnotte = db._accounts[self.cagnotte_id]
        service = cagnotte.services[self.service_id]

        # Si il y a une liste fermé de compte on check
        if service.authorized_rank is not None:
            if (
                self.user_id not in cagnotte.get_rank_list(service.authorized_rank)
                and self.user_id
                not in cagnotte.managers  # les managers font ce qu'ils veulent
            ):
                raise BadRankService(self.user_id)

        service.execute(db, self.user_id)


@attrs(frozen=True, kw_only=True)
class CancelService(Block):
    user_id = attrib(type=UserId, converter=UserId)
    cagnotte_id = attrib(type=CagnotteId, converter=CagnotteId)
    service_id = attrib(type=int)

    def execute(self, db: SwagChain):
        cagnotte = db._accounts[self.cagnotte_id]
        service = cagnotte.services[self.service_id]

        service.cancel(db, self.user_id)


@attrs(frozen=True, kw_only=True)
class ServiceDelation(Block):
    user_id = attrib(type=UserId, converter=UserId)
    cagnotte_id = attrib(type=CagnotteId, converter=CagnotteId)
    service_id = attrib(type=int)

    def execute(self, db: SwagChain):
        cagnotte = db._accounts[self.cagnotte_id]
        service = cagnotte.services[self.service_id]

        if self.user_id not in cagnotte.managers:
            raise NotCagnotteManager(self.user_id)

        for account_id, account in db._accounts.items():
            if service in account.subscribed_services:
                account.subscribed_services.remove(service)

        cagnotte.services.remove(service)
