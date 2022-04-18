import json
from typing import Dict
from attr import attrs, attrib
from arrow import Arrow
from disnake import TextChannel
import disnake
from swag.block import Block

from swag.blocks.yfu_blocks import YfuGenerationBlock

from .blockchain_parser import structure_block, unstructure_block
from .blockchain import SwagChain


def json_converter(o):
    if isinstance(o, Arrow):
        return o.__str__()


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
            if isinstance(block, YfuGenerationBlock):
                # Mise à jour de l'url de l'avatar dans la Yfu
                avatar_url = message.attachments[0].url
                synced_chain._yfus[block.yfu_id].avatar_url = avatar_url

        return synced_chain

    async def append(self, block):
        SwagChain.append(self, block)

        # Envoie de l'avatar si generation de Yfu
        if isinstance(block, YfuGenerationBlock):
            message = await self._channel.send(
                json.dumps(unstructure_block(block), default=json_converter),
                file=disnake.File(block.avatar_local_path),
            )
            # Mise à jour de l'url de l'avatar dans la Yfu
            avatar_url = message.attachments[0].url
            self._yfus[block.yfu_id].avatar_url = avatar_url
        else:
            message = await self._channel.send(
                json.dumps(unstructure_block(block), default=json_converter)
            )

        self._messages[block] = message.id
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
        print(f"Delation of {block}")
        await self._channel.get_partial_message(self._messages.pop(block)).delete()
        