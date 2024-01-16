import json
from pathlib import Path
from typing import Optional
import requests
import cbor2
from attr import attrs, attrib
from swag.block import Block
from git import Repo
import arrow
import time

from .blockchain_parser import structure_block, unstructure_block
from .blockchain import SwagChain


def get_assets(assets_url):
    r = requests.get(assets_url)
    if r.status_code == 200:
        return [
            i
            for sublist in (
                get_assets(f"{assets_url}{v['name']}/")
                if v["type"] == "directory"
                else [f"{assets_url}{v['name']}"]
                for v in json.loads(r.content)
            )
            for i in sublist
        ]
    else:
        print(r)
        raise ConnectionError("Shit just happened with the ¥fu assets")


@attrs
class GitSwagChain(SwagChain):
    _id: int = attrib()
    _path: str = attrib()
    _repo: Optional[Repo] = attrib()
    _repo_path: Optional[str] = attrib()

    @classmethod
    async def from_file(
        cls, bot_id: int, path: str, assets_url: str, repo: Optional[str] = None
    ):
        synced_chain = cls(
            [],
            get_assets(assets_url),
            bot_id,
            path,
            Repo(repo) if repo is not None else None,
            repo,
        )
        try:
            with open(path, "rb") as file:
                for unstructured_block in cbor2.load(file):
                    block = structure_block(unstructured_block)
                    try:
                        SwagChain.append(synced_chain, block)
                    except:
                        print("\n\n\033[91mERREUR SUR LA BLOCKCHAIN\033[0m\n\n")
        except FileNotFoundError:
            pass
        return synced_chain

    async def append(self, block):
        # Record the start time
        start_time = time.time()

        SwagChain.append(self, block)

        with open(self._path, "wb") as file:
            cbor2.dump(
                [unstructure_block(block) for block in self._chain],
                file,
            )

        if self._repo is not None:
            self._repo.index.add([Path(self._path).relative_to(self._repo_path)])
            self._repo.index.commit(str(arrow.now()))
            origin = self._repo.remote(name="origin")
            origin.push()

        # Record the end time
        end_time = time.time()

        # Calculate the time difference
        elapsed_time = end_time - start_time

        print(f"Elapsed Time: {elapsed_time:.5f} seconds")
