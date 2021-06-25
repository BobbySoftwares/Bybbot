from swag.db import SwagDB
from apscheduler.triggers.cron import CronTrigger
from decimal import Decimal

from .bank import (
    AlreadyMineToday,
    InvalidSwagValue,
    InvalidStyleValue,
    NoAccountRegistered,
    NotEnoughStyleInBalance,
    NotEnoughSwagInBalance,
    StyleStillBlocked,
    SwagBank,
    TIME_OF_BLOCK,
)
from .utils import mini_history_swag_message, update_forbes_classement, update_the_style

from utils import GUILD_ID_BOBBYCRATIE, format_number, reaction_message_building
from module import Module


class SwagClient(Module):
    def __init__(self, client, db_path) -> None:
        self.client = client
        print("Initialisation de la Banque Centrale du $wag...\n")
        self.swag_bank = SwagBank(db_path)
        self.the_swaggest = None

    async def setup(self):
        print("Mise à jour du classement et des bonus de blocage\n\n")
        await update_forbes_classement(
            self.client.get_guild(GUILD_ID_BOBBYCRATIE), self
        )

    async def add_jobs(self, scheduler):
        # Programme la fonction update_the_style pour être lancée
        # toutes les heures.
        async def job():
            await update_the_style(self.client, self)

        scheduler.add_job(job, CronTrigger(hour="*"))

    async def process(self, message):
        try:
            if message.content.startswith("!$wag"):
                await self.execute_swag_command(message)
            elif message.content.startswith("!$tyle"):
                await self.execute_style_command(message)
        except NotEnoughSwagInBalance:
            await message.channel.send(
                f"{message.author.mention} ! Tu ne possèdes pas assez de $wag pour "
                "faire cette transaction, vérifie ton solde avec `!$wag solde`"
            )
        except InvalidSwagValue:
            await message.channel.send(
                f"{message.author.mention}, la valeur que tu as écrite est "
                "incorrecte, elle doit être supérieur à 0 et entière, car le "
                "$wag est **indivisible** !"
            )
        except AlreadyMineToday:
            await message.channel.send(
                f"Désolé {message.author.mention}, mais tu as déjà miné du $wag "
                "aujourd'hui 😮 ! Reviens donc demain !"
            )
        except StyleStillBlocked:
            await message.channel.send(
                f"{message.author.mention}, du $wag est déjà bloqué à ton compte "
                "chez $tyle Generatoc Inc. ! Attends leurs déblocage pour pouvoir "
                "en bloquer de nouveau !"
            )
        except NotEnoughStyleInBalance:
            await message.channel.send(
                f"{message.author.mention} ! Tu ne possèdes pas assez de $tyle "
                "pour faire cette transaction, vérifie ton solde avec "
                "`!$tyle solde`"
            )
        except (InvalidStyleValue):
            await message.channel.send(
                f"{message.author.mention}, la valeur que tu as écrite est "
                "incorrecte, elle doit être supérieur à 0, car le $tyle est "
                "**toujours positif** !"
            )
        except (NoAccountRegistered) as e:
            await message.channel.send(
                f"{e.name}, tu ne possèdes pas de compte chez $wagBank™ "
                "<:rip:817165391846703114> !\n\n"
                "Remédie à ce problème en lançant la commande `!$wag créer` "
                "et devient véritablement $wag 😎!"
            )

    async def execute_swag_command(self, message):
        command_swag = message.content.split()

        if "créer" in command_swag:
            user = message.author
            self.swag_bank.add_user(user.id)
            await message.channel.send(
                f"Bienvenue chez $wagBank™ {user.mention} !\n\n"
                "Tu peux maintenant miner du $wag avec la commande `!$wag miner` 💰"
            )

        elif "miner" in command_swag:
            user = message.author
            mining_booty = self.swag_bank.mine(user.id)
            await message.channel.send(
                f"⛏ {user.mention} a miné `{format_number(mining_booty)} $wag` !"
            )
            await update_forbes_classement(message.guild, self)

        elif "info" in command_swag:
            user = message.author
            user_infos = self.swag_bank.get_account_info(user.id)

            # TODO : Changer l'affichage pour avoir une affichage à la bonne heure,
            # et en français
            release_info = (
                f"-Date du déblocage sur $wag : {user_infos.unblocking_date}\n"
                if user_infos.blocked_swag != 0
                else ""
            )
            await message.channel.send(
                "```diff\n"
                f"Relevé de compte de {message.author.display_name}\n"
                f"-$wag : {format_number(user_infos.swag_balance)}\n"
                f"-$tyle : {format_number(user_infos.style_balance)}\n"
                f"-Taux de bloquage : {format_number(user_infos.style_rate)} %\n"
                "-$wag actuellement bloqué : "
                f"{format_number(user_infos.blocked_swag)}\n"
                f"{release_info}"
                "```"
            )

        elif "historique" in command_swag:
            user = message.author
            history = self.swag_bank.get_history(user.id)
            await message.channel.send(
                f"{user.mention}, voici l'historique de tes transactions de $wag :\n"
            )
            await reaction_message_building(
                self.client, history, message, mini_history_swag_message
            )

        elif "payer" in command_swag:
            # Récupération du destinataire
            destinataire = message.mentions
            if len(destinataire) != 1:
                await message.channel.send(
                    "Merci de mentionner un destinataire (@Bobby Machin) "
                    "pour lui donner de ton $wag !"
                )
                return
            destinataire = destinataire[0]

            giver = message.author
            recipient = destinataire

            # Récupération de la valeur envoyé
            value = int(
                "".join(argent for argent in command_swag if argent.isnumeric())
            )

            # envoie du swag
            self.swag_bank.swag_transaction(giver.id, recipient.id, value)

            await message.channel.send(
                "Transaction effectué avec succès ! \n"
                "```ini\n"
                f"[{message.author.display_name}\t"
                f"{format_number(value)} $wag\t"
                f"-->\t{destinataire.display_name}]\n"
                "```"
            )
            await update_forbes_classement(message.guild, self)

        else:
            # Si l'utilisateur se trompe de commande, ce message s'envoie par défaut
            await message.channel.send(
                f"{message.author.mention}, tu sembles perdu, "
                "voici les commandes que tu peux utiliser avec ton $wag :\n"
                "```HTTP\n"
                "!$wag créer ~~ Crée un compte chez $wagBank™\n"
                "!$wag info ~~ Voir ton solde et toutes les infos de ton compte \n"
                "!$wag miner ~~ Gagner du $wag gratuitement tout les jours\n"
                "!$wag payer [montant] [@destinataire] ~~ Envoie un *montant* "
                "de $wag au *destinataire* spécifié\n"
                "!$wag historique ~~ Visualiser l'ensemble des transactions "
                "effectuées sur ton compte\n"
                "```"
            )
        await update_forbes_classement(message.guild, self)

    async def execute_style_command(self, message):
        command_style = message.content.split()
        if "bloquer" in command_style:
            # Récupération de la valeur envoyé
            user = message.author
            value = int(
                "".join(argent for argent in command_style if argent.isnumeric())
            )

            self.swag_bank.block_swag(user.id, value)

            await message.channel.send(
                f"{user.mention}, vous venez de bloquer "
                f"`{format_number(value)} $wag`, vous les "
                f"récupérerez dans **{TIME_OF_BLOCK} jours** à la même "
                "heure\n"
            )
            await update_forbes_classement(message.guild, self)

        elif "payer" in command_style:
            # Récupération du destinataire
            destinataire = message.mentions
            if len(destinataire) != 1:
                await message.channel.send(
                    "Merci de mentionner un destinataire (@Bobby Machin) pour "
                    "lui donner de ton $tyle !"
                )
                return
            destinataire = destinataire[0]

            giver = message.author
            recipient = destinataire

            # Récupération de la valeur envoyé
            value = Decimal(
                "".join(
                    argent
                    for argent in command_style
                    if argent.replace(".", "").replace(",", "").isnumeric()
                )
            )

            # envoie du style
            self.swag_bank.style_transaction(giver.id, recipient.id, value)

            await message.channel.send(
                "Transaction effectué avec succès ! \n"
                "```ini\n"
                f"[{message.author.display_name}\t"
                f"{format_number(value)} $tyle\t"
                f"-->\t{destinataire.display_name}]\n"
                "```"
            )
            await update_forbes_classement(message.guild, self)

        else:
            await message.channel.send(
                f"{message.author.mention}, tu sembles perdu, voici les "
                "commandes que tu peux utiliser avec en relation avec ton "
                "$tyle :\n"
                "```HTTP\n"
                "!$tyle payer [montant] [@destinataire] ~~ Envoie un *montant* "
                "de $tyle au *destinataire* spécifié\n"
                "!$tyle bloquer [montant] ~~ Bloque un *montant* de $wag pour "
                "générer du $tyle pendant quelques jours\n"
                "```"
            )