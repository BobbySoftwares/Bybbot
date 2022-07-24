import json
from typing import Dict
from attr import attrs, attrib
from arrow import Arrow

from disnake import TextChannel
import disnake
from swag.block import Block


from .blockchain_parser import structure_block, unstructure_block
from .blockchain import SwagChain, json_converter
@attrs
class SyncedSwagChain(SwagChain):
    _id: int = attrib()
    _channel: TextChannel = attrib(init=False, default=None)
    _messages: Dict[int,Block] = attrib(init=False, default={})

    @classmethod
    async def from_channel(cls, bot_id: int, channel: TextChannel):
        synced_chain = cls([], bot_id)
        synced_chain._channel = channel
        synced_chain._messages = {}
        async for message in channel.history(limit=None, oldest_first=True):
            unstructured_block = json.loads(message.content)
            block = structure_block(unstructured_block)
            SwagChain.append(synced_chain, block)
            synced_chain._messages[block] = message.id
        return synced_chain

    async def append(self, block):
        SwagChain.append(self, block)
        await self._channel.send(
            json.dumps(unstructure_block(block), default=json_converter)
        )
        # try:
        #     self._chain.append(block)
        #     await self._channel.send(json.dumps(unstructure_block(block)))
        # except AttributeError:
        #     raise ValueError(
        #         "Trying to call `append` on a `SyncedSwagChain` instance not "
        #         "bound to a TextChannel. Please use SyncedSwagChain.from_channel "
        #         "to create a bounded instance."
        #     )

    async def remove(self, block):
        SwagChain.remove(self,block)
        print(f"Deletion of {block}")
        await self._channel.get_partial_message(self._messages.pop(block)).delete()