from typing import Dict, Union

from swag.currencies import Style, Swag
from swag.id import CagnotteId, UserId

# from cattr import structure, unstructure
from .. import blocks
from cattrs_extras.converter import Converter

converter = Converter()


def unstructure_money(o):
    return [o.currency, converter.unstructure(o.value)]


def structure_money(o, t):
    converter.structure(o, Swag if t.currency in o else Style)


def structure_id(o, _):
    try:
        return UserId(int(o))
    except ValueError:
        return CagnotteId(o)


def unstructure_id(o):
    return o.id


converter.register_unstructure_hook(Swag, unstructure_money)
converter.register_unstructure_hook(Style, unstructure_money)
converter.register_unstructure_hook(UserId, unstructure_id)
converter.register_unstructure_hook(CagnotteId, unstructure_id)

converter.register_structure_hook(Swag, lambda o, _: Swag(o[1]))
converter.register_structure_hook(Style, lambda o, _: Style(o[1]))
converter.register_structure_hook(
    Union[Swag, Style],
    lambda o, _: converter.structure(o, Swag if o[0] == "$wag" else Style),
)
converter.register_structure_hook(UserId, lambda o, _: UserId(o))
converter.register_structure_hook(CagnotteId, lambda o, _: CagnotteId(o))
converter.register_structure_hook(Union[UserId, CagnotteId], structure_id)

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