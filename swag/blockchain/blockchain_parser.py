from decimal import Decimal
from typing import Any, Dict, List, Type, Union
from swag import powers

from swag.artefacts.accounts import CagnotteRank
from swag.artefacts.services import Payment, Service
from swag.currencies import Style, Swag
from swag.id import AccountId, CagnotteId, GenericId, UserId, YfuId, get_id_from_str
from swag.powers.power import Power

# from cattr import structure, unstructure
from .. import blocks
from cattr import Converter

converter = Converter()


def unstructure_money(o):
    return [o._CURRENCY, converter.unstructure(o.value)]


def structure_money(o, t):
    converter.structure(o, Swag if t._CURRENCY in o else Style)


def structure_id(o, _):
    return get_id_from_str(str(o))


def unstructure_id(o):
    return o.id


def structure_decimal(obj: Any, cls: Type) -> Decimal:
    return cls(str(obj))


def unstructure_decimal(obj: Decimal) -> str:
    return str(obj)


available_power = {
    name: cls for name, cls in powers.__dict__.items() if isinstance(cls, type)
}


def structure_power(obj: Any, cls: Type) -> Power:
    power_class = available_power[obj[0]]
    return power_class(int(obj[1]))


def unstructure_power(obj: Power) -> str:
    return [type(obj).__name__, str(obj.power_points)]


converter.register_structure_hook(Decimal, structure_decimal)
converter.register_unstructure_hook(Decimal, unstructure_decimal)

converter.register_structure_hook(Power, structure_power)
converter.register_unstructure_hook(Power, unstructure_power)

converter.register_unstructure_hook(Swag, unstructure_money)
converter.register_unstructure_hook(Style, unstructure_money)
converter.register_unstructure_hook(UserId, unstructure_id)
converter.register_unstructure_hook(CagnotteId, unstructure_id)
converter.register_unstructure_hook(YfuId, unstructure_id)

converter.register_structure_hook(Swag, lambda o, _: Swag(o[1]))
converter.register_structure_hook(Style, lambda o, _: Style(o[1]))
converter.register_structure_hook(
    Union[Swag, Style],
    lambda o, _: converter.structure(o, Swag if o[0] == "$wag" else Style),
)
converter.register_structure_hook(UserId, lambda o, _: UserId(o))
converter.register_structure_hook(CagnotteId, lambda o, _: CagnotteId(o))
converter.register_structure_hook(YfuId, lambda o, _: YfuId(o))
converter.register_structure_hook(AccountId, structure_id)
converter.register_structure_hook(GenericId, structure_id)


available_payment = {
    payment_subclasses.__name__: payment_subclasses
    for payment_subclasses in Payment.__subclasses__()
    if isinstance(payment_subclasses, type)
}


def structure_payment(obj: Any, cls: Type) -> Payment:
    payment_class = available_payment[obj[0]]

    payment = payment_class(**obj[1])

    # Structure all the money if attribut name is amount
    if hasattr(payment, "amount"):
        payment.amount = converter.structure(payment.amount, Union[Swag, Style])

    return payment


def unstructure_payment(obj: Payment) -> str:
    return [type(obj).__name__, converter.unstructure(obj.__dict__)]


available_service = {
    service_subclasses.__name__: service_subclasses
    for service_subclasses in Service.__subclasses__()
    if isinstance(service_subclasses, type)
}


def structure_service(obj: Any, cls: Type) -> Service:
    service_class = available_service[obj[0]]
    service = service_class(**obj[1])

    # Structure all the costs
    service.costs = [converter.structure(cost, Payment) for cost in service.costs]

    return service


def unstructure_service(obj: Service) -> str:
    return [type(obj).__name__, converter.unstructure(obj.__dict__)]


converter.register_unstructure_hook(Payment, unstructure_payment)
converter.register_structure_hook(Payment, structure_payment)
converter.register_unstructure_hook(Service, unstructure_service)
converter.register_structure_hook(Service, structure_service)


def unstructure_cagnotte_rank(obj: CagnotteRank) -> Dict:
    return obj.__dict__


def structure_cagnotte_rank(obj: Dict, cls: Type) -> CagnotteRank:
    return CagnotteRank(**obj)


converter.register_unstructure_hook(CagnotteRank, unstructure_cagnotte_rank)
converter.register_structure_hook(CagnotteRank, structure_cagnotte_rank)

block_types = {
    name: cls for name, cls in blocks.__dict__.items() if isinstance(cls, type)
}


def structure_block(unstructured_block: Dict):
    print(unstructured_block)
    block_type = block_types[unstructured_block.pop("block_type")]
    return converter.structure(unstructured_block, block_type)


def unstructure_block(structured_block):
    return {
        "block_type": type(structured_block).__name__,
        **converter.unstructure(structured_block),
    }
