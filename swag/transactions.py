from enum import IntEnum


class TransactionType(IntEnum):
    CREATION = 0
    MINE = 1
    SWAG = 2
    STYLE = 3
    BLOCK = 4
    RELEASE = 5
    ROI = 6
    DONATION = 7  # Envoie de l'argent à une cagnotte
    DISTRIBUTION = 8  # Recevoir de l'argent depuis cagnotte


def concerns_user(id, transaction):
    if transaction[1] == TransactionType.CREATION:
        return id == transaction[2]
    elif transaction[1] == TransactionType.MINE:
        return id == transaction[2][0]
    elif transaction[1] == TransactionType.SWAG:
        return id == transaction[2][0] or id == transaction[2][1]
    elif transaction[1] == TransactionType.STYLE:
        return id == transaction[2][0] or id == transaction[2][1]
    elif transaction[1] == TransactionType.BLOCK:
        return id == transaction[2][0]
    elif transaction[1] == TransactionType.RELEASE:
        return id == transaction[2][0]
    elif transaction[1] == TransactionType.ROI:
        return id == transaction[2][0]
    elif transaction[1] == TransactionType.DONATION:
        return id == transaction[2][0]
    elif transaction[1] == TransactionType.DISTRIBUTION:
        return id == transaction[2][1]


def concerns_cagnotte(id, transaction):
    if transaction[1] == TransactionType.DONATION:
        return id == transaction[2][1]
    elif transaction[1] == TransactionType.DISTRIBUTION:
        return id == transaction[2][0]
