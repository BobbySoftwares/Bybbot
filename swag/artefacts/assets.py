class AssetNotFound(Exception):
    pass


class AssetDict(dict):
    def __missing__(self, key):
        raise AssetNotFound(key)