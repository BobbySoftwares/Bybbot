import json
import cbor2
from attr import attrs, attrib
from arrow import Arrow
from disnake import TextChannel
import disnake
from swag.blocks.system_blocks import AssetUploadBlock

from .blockchain_parser import structure_block, unstructure_block
from .blockchain import SwagChain


def json_converter(o):
    if isinstance(o, Arrow):
        return o.__str__()


@attrs
class SyncedSwagChain(SwagChain):
    _id: int = attrib()
    _channel: TextChannel = attrib(init=False, default=None)

    @classmethod
    async def from_channel(cls, bot_id: int, channel: TextChannel):
        synced_chain = cls([], bot_id)
        synced_chain._channel = channel
        async for message in channel.history(limit=None, oldest_first=True):
            unstructured_block = json.loads(message.content)
            block = structure_block(unstructured_block)
            SwagChain.append(synced_chain, block)
            if isinstance(block, AssetUploadBlock):
                # Mise à jour de la bibliothèque des assets
                asset_url = message.attachments[0].url
                synced_chain._assets[block.asset_key] = asset_url

        return synced_chain

    async def append(self, block):
        SwagChain.append(self, block)

        # Envoie de l'asset si le block est une demande d'upload d'asset
        if isinstance(block, AssetUploadBlock):
            asset_message = await self._channel.send(
                json.dumps(unstructure_block(block), default=json_converter),
                file=disnake.File(block.local_path),
            )
            # Mise à jour de la bibliothèque des assets
            asset_url = asset_message.attachments[0].url
            self._assets[block.asset_key] = asset_url
        else:
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

    async def save_backup(self):
        unstructured_blocks = []

        async for message in self._channel.history(limit=None, oldest_first=True):
            unstructured_blocks.append(json.loads(message.content))
        
        with open('swagchain.bk', 'wb') as backup_file:
            cbor2.dump(unstructured_blocks, backup_file)