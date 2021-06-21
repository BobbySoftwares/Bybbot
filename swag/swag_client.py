from apscheduler.triggers.cron import CronTrigger

from .swag import (
    AlreadyMineToday,
    InvalidValue,
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
    def __init__(self, client) -> None:
        self.client = client
        print("Initialisation de la Banque Centrale du $wag...\n")
        self.swag_bank = SwagBank()

    async def setup(self):
        print("Mise à jour du classement et des bonus de blocage\n\n")
        await update_forbes_classement(
            self.client.get_guild(GUILD_ID_BOBBYCRATIE), self.swag_bank
        )

    async def add_jobs(self, scheduler):
        # Programme la fonction update_the_style pour être lancée
        # toutes les heures.
        async def job():
            await update_the_style(self.client, self.swag_bank)

        scheduler.add_job(job, CronTrigger(hour="*"))

    async def process(self, message):
        if message.content.startswith("!$wag"):
            await self.execute_swag_command(message)
        elif message.content.startswith("!$tyle"):
            await self.execute_style_command(message)

    async def execute_swag_command(self, message):
        command_swag = message.content.split()

        try:
            if "créer" in command_swag:
                self.swag_bank.add_account(str(message.author))
                await message.channel.send(
                    f"Bienvenue chez $wagBank™ {message.author.mention} !\n\n"
                    "Tu peux maintenant miner du $wag avec la commande `!$wag miner` 💰"
                )

            elif "bourrer" in command_swag:
                self.swag_bank.add_account(str(message.mentions[0]))
                await message.channel.send(
                    f"Bienvenue chez $wagBank™ {message.mentions[0]} !\n\n"
                    "Tu peux maintenant miner du $wag avec la commande `!$wag miner` 💰"
                )

            elif "nimer" in command_swag:
                message.author = message.mentions[0]
                mining_booty = self.swag_bank.mine(str(message.author))
                await message.channel.send(
                    f"⛏ {message.author.mention} a miné `{format_number(mining_booty)} $wag` !"
                )
                await update_forbes_classement(message.guild, self.swag_bank)

            elif "miner" in command_swag:
                mining_booty = self.swag_bank.mine(str(message.author))
                await message.channel.send(
                    f"⛏ {message.author.mention} a miné `{format_number(mining_booty)} $wag` !"
                )
                await update_forbes_classement(message.guild, self.swag_bank)

            elif "solde" in command_swag:
                montant_swag = self.swag_bank.get_balance_of(str(message.author))
                await message.channel.send(
                    "```diff\n"
                    f"$wag de {message.author.display_name} : {format_number(montant_swag)}\n"
                    "```"
                )

            elif "historique" in command_swag:
                history = self.swag_bank.get_history(str(message.author))
                await message.channel.send(
                    f"{message.author.mention}, voici l'historique de tes transactions de $wag :\n"
                )
                await reaction_message_building(
                    self.client, history, message, mini_history_swag_message
                )

            elif "payer" in command_swag:
                # Récupération du destinataire
                destinataire = message.mentions
                if len(destinataire) != 1:
                    await message.channel.send(
                        "Merci de mentionner un destinataire (@Bobby Machin) pour lui donner de ton $wag !"
                    )
                    return

                # Récupération de la valeur envoyé
                valeur = [argent for argent in command_swag if argent.isnumeric()]
                if len(valeur) != 1:
                    raise InvalidValue

                # envoie du swag
                self.swag_bank.give_swag(
                    str(message.author),
                    str(destinataire[0]),
                    int(valeur[0]),
                )
                await message.channel.send(
                    "Transaction effectué avec succès ! \n"
                    "```ini\n"
                    f"[{message.author.display_name}\t{format_number(int(valeur[0]))} $wag\t-->\t{destinataire[0].display_name}]\n"
                    "```"
                )
                await update_forbes_classement(message.guild, self.swag_bank)
            else:
                # Si l'utilisateur se trompe de commande, ce message s'envoie par défaut
                await message.channel.send(
                    f"{message.author.mention}, tu sembles perdu, voici les commandes que tu peux utiliser avec ton $wag :\n"
                    "```HTTP\n"
                    "!$wag créer ~~ Crée un compte chez $wagBank™\n"
                    "!$wag solde ~~ Voir ton solde de $wag sur ton compte\n"
                    "!$wag miner ~~ Gagner du $wag gratuitement tout les jours\n"
                    "!$wag payer [montant] [@destinataire] ~~ Envoie un *montant* de $wag au *destinataire* spécifié\n"
                    "!$wag historique ~~ Visualiser l'ensemble des transactions effectuées sur ton compte\n"
                    "```"
                )

        except NotEnoughSwagInBalance:
            await message.channel.send(
                f"{message.author.mention} ! Tu ne possèdes pas assez de $wag pour faire cette transaction, vérifie ton solde avec `!$wag solde`"
            )
        except InvalidValue:
            await message.channel.send(
                f"{message.author.mention}, la valeur que tu as écrite est incorrecte, elle doit être supérieur à 0 et entière, car le $wag est **indivisible** !"
            )
        except AlreadyMineToday:
            await message.channel.send(
                f"Désolé {message.author.mention}, mais tu as déjà miné du $wag aujourd'hui 😮 ! Reviens donc demain !"
            )
        except NoAccountRegistered as e:
            await message.channel.send(
                f"{e.name}, tu ne possèdes pas de compte chez $wagBank™ <:rip:817165391846703114> !\n\n"
                "Remédie à ce problème en lançant la commande `!$wag créer` et devient véritablement $wag 😎!"
            )
        await update_forbes_classement(message.guild, self.swag_bank)

    async def execute_style_command(self, message):
        command_style = message.content.split()

        try:
            if "info" in command_style:
                style_amount = self.swag_bank.get_style_balance_of(str(message.author))
                growth_rate = self.swag_bank.get_style_total_growth_rate(
                    str(message.author)
                )
                blocked_swag = self.swag_bank.get_bloked_swag(str(message.author))
                # TODO : Changer l'affichage pour avoir une affichage à la bonne heure, et en français
                release_info = (
                    f"-Date du déblocage sur $wag : {self.swag_bank.get_date_of_unblocking_swag(str(message.author))}\n"
                    if self.swag_bank.is_blocking_swag(str(message.author))
                    else ""
                )
                await message.channel.send(
                    "```diff\n"
                    f"$tyle de {message.author.display_name} : {format_number(style_amount)}\n"
                    f"-Taux de bloquage : {format_number(growth_rate)} %\n"
                    f"-$wag actuellement bloqué : {format_number(blocked_swag)}\n"
                    f"{release_info}"
                    "```"
                )

            elif "bloquer" in command_style:
                # Récupération de la valeur envoyé
                valeur = [argent for argent in command_style if argent.isnumeric()]
                if len(valeur) != 1:
                    raise InvalidValue

                self.swag_bank.block_swag_to_get_style(
                    str(message.author), int(valeur[0])
                )
                await message.channel.send(
                    f"{message.author.mention}, vous venez de bloquer `{format_number(int(valeur[0]))}$wag` vous les récupérerez dans **{TIME_OF_BLOCK} jours** à la même heure\n"
                )
                await update_forbes_classement(message.guild, self.swag_bank)

            elif "payer" in command_style:
                # Récupération du destinataire
                destinataire = message.mentions
                if len(destinataire) != 1:
                    await message.channel.send(
                        "Merci de mentionner un destinataire (@Bobby Machin) pour lui donner de ton $tyle !"
                    )
                    return

                # Récupération de la valeur envoyé
                valeur = [
                    argent
                    for argent in command_style
                    if argent.replace(".", "").replace(",", "").isnumeric()
                ]
                if len(valeur) != 1:
                    raise InvalidValue

                # envoie du style
                self.swag_bank.give_style(
                    str(message.author),
                    str(destinataire[0]),
                    float(valeur[0]),
                )
                await message.channel.send(
                    "Transaction effectué avec succès ! \n"
                    "```ini\n"
                    f"[{message.author.display_name}\t{format_number(float(valeur[0]))} $tyle\t-->\t{destinataire[0].display_name}]\n"
                    "```"
                )
                await update_forbes_classement(message.guild, self.swag_bank)
            else:
                await message.channel.send(
                    f"{message.author.mention}, tu sembles perdu, voici les commandes que tu peux utiliser avec en relation avec ton $tyle :\n"
                    "```HTTP\n"
                    "!$tyle info ~~ Voir ton solde de $tyle, ton bonus de bloquage, le $wag que tu as bloqué, et la date de déblocage \n"
                    "!$tyle payer [montant] [@destinataire] ~~ Envoie un *montant* de $tyle au *destinataire* spécifié\n"
                    "!$tyle bloquer [montant] ~~ Bloque un *montant* de $wag pour générer du $tyle pendant quelques jours\n"
                    "```"
                )
        except StyleStillBlocked:
            await message.channel.send(
                f"{message.author.mention}, du $wag est déjà bloqué à ton compte chez $tyle Generatoc Inc. ! Attends leurs déblocage pour pouvoir en bloquer de nouveau !"
            )
        except InvalidValue:
            await message.channel.send(
                f"{message.author.mention}, la valeur que tu as écrite est incorrecte, elle doit être supérieur à 0 et entière, car le $wag est **indivisible** !"
            )
        except NotEnoughSwagInBalance:
            await message.channel.send(
                f"{message.author.mention} ! Tu ne possèdes pas assez de $wag pour faire cette transaction, vérifie ton solde avec `!$wag solde`"
            )
        except NotEnoughStyleInBalance:
            await message.channel.send(
                f"{message.author.mention} ! Tu ne possèdes pas assez de $tyle pour faire cette transaction, vérifie ton solde avec `!$tyle solde`"
            )
        except (InvalidValue):
            await message.channel.send(
                f"{message.author.mention}, la valeur que tu as écrite est incorrecte, elle doit être supérieur à 0, car le $tyle est **toujours positif** !"
            )
        except (NoAccountRegistered) as e:
            await message.channel.send(
                f"{e.name}, tu ne possèdes pas de compte chez $wagBank™ <:rip:817165391846703114> !\n\n"
                "Remédie à ce problème en lançant la commande `!$wag créer` et devient véritablement $wag 😎!"
            )
