from swag.errors import (
    CagnotteNameAlreadyExist,
    DestructionOfNonEmptyCagnotte,
    NoCagnotteIdxInCommand,
    NoCagnotteRegistered,
    NotEnoughMoneyInCagnotte,
    NotInGestionnaireGroupCagnotte,
)
from apscheduler.triggers.cron import CronTrigger
from decimal import Decimal, ROUND_DOWN
from arrow import utcnow

from .bank import (
    AlreadyMineToday,
    InvalidSwagValue,
    InvalidStyleValue,
    InvalidTimeZone,
    TimeZoneFieldLocked,
    NoAccountRegistered,
    AccountAlreadyExist,
    NotEnoughStyleInBalance,
    NotEnoughSwagInBalance,
    StyleStillBlocked,
    SwagBank,
    BLOCKING_TIME,
)
from .utils import mini_history_swag_message, update_forbes_classement, update_the_style

from utils import (
    GUILD_ID_BOBBYCRATIE,
    format_number,
    get_guild_member_name,
    reaction_message_building,
)
from module import Module


class SwagClient(Module):
    def __init__(self, client, db_path) -> None:
        self.client = client
        print("Initialisation de la Banque Centrale du $wag...\n")
        self.swag_bank = SwagBank(db_path)
        self.the_swaggest = None
        self.last_update = None

    async def setup(self):
        print("Mise à jour du classement et des bonus de blocage\n\n")
        await update_forbes_classement(
            self.client.get_guild(GUILD_ID_BOBBYCRATIE), self, self.client
        )

    async def add_jobs(self, scheduler):
        # Programme la fonction update_the_style pour être lancée
        # toutes les heures.
        async def job():
            now = utcnow().replace(microsecond=0, second=0, minute=0)
            if self.last_update is None or self.last_update < now:
                self.last_update = now
                await update_the_style(self.client, self)

        scheduler.add_job(job, CronTrigger(hour="*"))

    async def process(self, message):
        try:
            if message.content.startswith("!$wagdmin"):
                await self.execute_swagdmin_command(message)
            elif message.content.startswith("!$wag"):
                await self.execute_swag_command(message)
            elif message.content.startswith("!$tyle"):
                await self.execute_style_command(message)
            elif message.content.startswith("!€agnotte"):
                await self.execute_cagnotte_command(message)
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
                "chez $tyle Generator Inc. ! Attends leurs déblocage pour pouvoir "
                "en bloquer de nouveau !"
            )
        except NotEnoughStyleInBalance:
            await message.channel.send(
                f"{message.author.mention} ! Tu ne possèdes pas assez de $tyle "
                "pour faire cette transaction, vérifie ton solde avec "
                "`!$tyle solde`"
            )
        except InvalidStyleValue:
            await message.channel.send(
                f"{message.author.mention}, la valeur que tu as écrite est "
                "incorrecte, elle doit être supérieur à 0, car le $tyle est "
                "**toujours positif** !"
            )
        except NoAccountRegistered as e:
            await message.channel.send(
                f"<@{e.name}>, tu ne possèdes pas de compte chez $wagBank™ "
                "<:rip:817165391846703114> !\n\n"
                "Remédie à ce problème en lançant la commande `!$wag créer` "
                "et devient véritablement $wag 😎!"
            )
        except AccountAlreadyExist:
            await message.channel.send(
                f"{message.author.mention}, tu possèdes déjà un compte chez $wagBank™ !"
            )
        except InvalidTimeZone as e:
            await message.channel.send(
                f"{e.name}, n'est pas un nom de timezone valide !\n"
                "Vérifie le nom correct sur "
                "https://en.wikipedia.org/wiki/List_of_tz_database_time_zones, "
                "à la colone `TZ database name`."
            )
        except TimeZoneFieldLocked as e:
            await message.channel.send(
                "Tu viens déjà de changer de timezone. Tu ne pourras effectuer "
                f"à nouveau cette opération qu'après le {e.date}. Cette mesure "
                "vise à empécher l'abus de minage, merci de ta compréhension.\n\n"
                "*L'abus de minage est dangereux pour la santé. À Miner avec "
                "modération. Ceci était un message de la Fédération Bobbyique du "
                "Minage*"
            )
        except NoCagnotteRegistered as e:
            await message.channel.send(
                f"Aucune €agnotte n°€{e.name} est active dans la $wagBank ! "
                f"{message.author.mention}, tu t'es sans doute trompé de numéro 🤨"
            )
        except NoCagnotteIdxInCommand as e:
            await message.channel.send(
                "Aucun numéro de cagnotte n'est mentionné avec la forme €n (ex : €1)"
                f"dans ta commande {message.author.mention}. 🤔"
            )
        except CagnotteNameAlreadyExist:
            await message.channel.send(
                f"{message.author.mention}, une €agnotte porte déjà ce nom ! "
                "Je te conseille de choisir un autre nom avant que tout le monde "
                "soit complètement duper 🤦‍♂️"
            )
        except NotEnoughMoneyInCagnotte:
            await message.channel.send(
                f"{message.author.mention}, tu es en train de demander à une €agnotte "
                "une somme d'argent qu'elle n'a pas. Non mais tu n'as pas honte ? 😐"
            )
        except NotInGestionnaireGroupCagnotte:
            await message.channel.send(
                f"{message.author.mention}, tu ne fais pas partie des gestionnaires "
                "de cette €agnotte, tu ne peux donc pas distribuer son contenu 🤷‍♀️"
            )
        except DestructionOfNonEmptyCagnotte:
            await message.channel.send(
                f"**Ligne 340 des conditions générales d'utilisations des €agnottes :**\n\n"
                "*Il est formellement interdit de détruire une cagnotte qui n'est pas vidée "
                "de son contenu. C'est comme ça.*"
            )

    async def execute_swag_command(self, message):
        command_swag = message.content.split()

        if "créer" in command_swag:
            user = message.author
            guild = message.guild
            self.swag_bank.add_user(user.id, guild.id)
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
            await update_forbes_classement(message.guild, self, self.client)

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
                f"-$tyle généré : {format_number(user_infos.pending_style)}\n"
                f"{release_info}"
                f"-Timezone du compte : {user_infos.timezone}"
                "```"
            )

        elif "historique" in command_swag:
            user = message.author
            user_account = self.swag_bank.get_account_info(user.id)
            history = list(reversed(self.swag_bank.get_history(user.id)))
            await message.channel.send(
                f"{user.mention}, voici l'historique de tes transactions de $wag :\n"
            )
            await reaction_message_building(
                self.client,
                history,
                message,
                mini_history_swag_message,
                self.swag_bank,
                user_account.timezone,
            )

        elif "bloquer" in command_swag:
            # Récupération de la valeur envoyé
            user = message.author
            try:
                value = int(
                    "".join(argent for argent in command_swag if argent.isnumeric())
                )
            except ValueError:
                raise InvalidSwagValue

            self.swag_bank.block_swag(user.id, value)

            await message.channel.send(
                f"{user.mention}, vous venez de bloquer "
                f"`{format_number(value)} $wag`, vous les "
                f"récupérerez dans **{BLOCKING_TIME} jours** à la même "
                "heure\n"
            )
            await update_forbes_classement(message.guild, self, self.client)

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
            try:
                value = int(
                    "".join(argent for argent in command_swag if argent.isnumeric())
                )
            except ValueError:
                raise InvalidSwagValue

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
            await update_forbes_classement(message.guild, self, self.client)

        elif "timezone" in command_swag:
            timezone = command_swag[2]
            user = message.author

            date = self.swag_bank.set_timezone(user.id, timezone)
            await message.channel.send(
                f"Ta timezone est désormais {timezone} !\n"
                "Pour des raisons de sécurité, tu ne pourras plus changer celle-ci "
                f"avant {date}. Merci de ta compréhension."
            )

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
                "!$wag bloquer [montant] ~~ Bloque un *montant* de $wag pour "
                "générer du $tyle pendant quelques jours\n"
                "!$wag historique ~~ Visualiser l'ensemble des transactions "
                "effectuées sur ton compte\n"
                "```"
            )
        await update_forbes_classement(message.guild, self, self.client)

    async def execute_style_command(self, message):
        command_style = message.content.split()
        if "bloquer" in command_style:
            # Récupération de la valeur envoyé
            user = message.author

            try:
                value = int(
                    "".join(argent for argent in command_style if argent.isnumeric())
                )
            except ValueError:
                raise InvalidSwagValue

            self.swag_bank.block_swag(user.id, value)

            await message.channel.send(
                f"{user.mention}, vous venez de bloquer "
                f"`{format_number(value)} $wag`, vous les "
                f"récupérerez dans **{BLOCKING_TIME} jours** à la même "
                "heure\n"
            )
            await update_forbes_classement(message.guild, self, self.client)

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
            try:
                value = Decimal(
                    "".join(
                        argent
                        for argent in command_style
                        if argent.replace(".", "").replace(",", "").isnumeric()
                    )
                ).quantize(Decimal(".0001"), rounding=ROUND_DOWN)
            except ValueError:
                raise InvalidStyleValue

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
            await update_forbes_classement(message.guild, self, self.client)

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

    async def execute_swagdmin_command(self, message):
        user = message.author
        guild = message.guild

        if not user.guild_permissions.administrator:
            return

        command = message.content.split()
        if "timezone" in command:
            timezone = command[2]

            self.swag_bank.set_guild_timezone(guild.id, timezone)
            await message.channel.send(
                f"La timezone par défaut du serveur est désormais {timezone}.\n"
                "Les futurs comptes SwagBank créés sur ce serveur seront "
                "configurés pour utiliser cette timezone par défaut."
            )

        elif "jobs" in command:
            await update_the_style(self.client, self)

        else:
            await message.channel.send(
                f"{message.author.mention}, tu sembles perdu, voici les "
                "commandes administrateur que tu peux utiliser avec en relation "
                "avec le $wag\n"
                "```HTTP\n"
                "!$wagdmin timezone [timezone] ~~ Configure la timezone par défaut "
                "du serveur\n"
                "```"
            )

    async def execute_cagnotte_command(self, message):
        def get_cagnotte_idx_from_command(splited_command):
            cagnotte_idx = int(
                [
                    identifiant[1:]
                    for identifiant in splited_command
                    if identifiant.startswith("€") and identifiant[1:].isnumeric()
                ][0]
            )
            return cagnotte_idx

        message_command = message.content
        splited_command = message_command.split()

        if "créer $wag" in message_command:
            cagnotte_name = " ".join(splited_command[3:])
            if len(cagnotte_name) == 0:
                await message.channel.send(
                    "Merci de mentionner un nom pour ta €agnotte."
                )
                return
            self.swag_bank.create_cagnotte(cagnotte_name, "$wag", message.author.id)

            cagnotte_id = (
                self.swag_bank.swagdb.get_cagnotte(cagnotte_name).get_info().id
            )
            await message.channel.send(
                f"{message.author.mention} vient de créer une €agnotte de $tyle nommée **« {cagnotte_name} »**. "
                f"Son identifiant est le €{cagnotte_id}"
            )

            await update_forbes_classement(message.guild, self, self.client)

        elif "créer $tyle" in message_command:
            cagnotte_name = " ".join(splited_command[3:])
            if len(cagnotte_name) == 0:
                await message.channel.send(
                    "Merci de mentionner un nom pour ta €agnotte."
                )
                return
            self.swag_bank.create_cagnotte(cagnotte_name, "$wag", message.author.id)

            cagnotte_id = (
                self.swag_bank.swagdb.get_cagnotte(cagnotte_name).get_info().id
            )
            await message.channel.send(
                f"{message.author.mention} vient de créer une €agnotte de $tyle nommée **« {cagnotte_name} »**. "
                f"Son identifiant est le €{cagnotte_id}"
            )
            await update_forbes_classement(message.guild, self, self.client)

        elif "créer" in splited_command:
            await message.channel.send(
                "Merci de mentionner le type de monnaie de la €agnotte "
                "après le mot clef **créer**"
            )

        elif set(splited_command).intersection(
            {"info", "historique", "payer", "donner", "loto", "partager", "détruire"}
        ) and all(
            "€" not in argument for argument in splited_command[1:]
        ):  # À partir d'ici, toute les commandes passe par l'identifiant de €agnotte (sous forme de €n)
            await message.channel.send(
                f"{message.author.mention}, il manque l'identifiant de la €agnotte"
                " dans la commande (€3 par exemple) afin de pouvoir faire l'action que tu demandes."
            )

        elif "info" in splited_command:
            cagnotte_idx = get_cagnotte_idx_from_command(splited_command)
            cagnotte_info = self.swag_bank.get_active_cagnotte(cagnotte_idx).get_info()
            await message.channel.send(
                f"Voici les informations de la €agnotte €{cagnotte_idx}\n"
                "```\n"
                f"Nom de €agnotte : {cagnotte_info.name}\n"
                f"Type de €agnotte : {cagnotte_info.currency}\n"
                f"Montant de la €agnotte : {cagnotte_info.balance} {cagnotte_info.currency}\n"
                f"Gestionnaire de la €agnotte : {[await get_guild_member_name(manager,message.guild,self.client) for manager in cagnotte_info.manager]}\n"
                f"Participants : {[await get_guild_member_name(participant,message.guild,self.client) for participant in cagnotte_info.participant]}\n"
                "```"
            )

        elif "historique" in splited_command:
            user = message.author
            user_account = self.swag_bank.get_account_info(user.id)

            cagnotte_idx = get_cagnotte_idx_from_command(splited_command)
            cagnotte_name = (
                self.swag_bank.get_active_cagnotte(cagnotte_idx).get_info().name
            )
            history = list(reversed(self.swag_bank.get_cagnotte_history(cagnotte_idx)))
            await message.channel.send(
                f"{message.author.mention}, voici l'historique de tes transactions de la cagnotte **{cagnotte_name}** :\n"
            )
            await reaction_message_building(
                self.client,
                history,
                message,
                mini_history_swag_message,
                self.swag_bank,
                user_account.timezone,
            )

        elif "payer" in splited_command:

            cagnotte_idx = get_cagnotte_idx_from_command(splited_command)

            currency = (
                self.swag_bank.get_active_cagnotte(cagnotte_idx).get_info().currency
            )

            if currency == "$wag":
                try:
                    value = int(
                        "".join(
                            argent for argent in splited_command if argent.isnumeric()
                        )
                    )
                except ValueError:
                    raise InvalidSwagValue

            elif currency == "$tyle":
                try:
                    value = Decimal(
                        "".join(
                            argent
                            for argent in splited_command
                            if argent.replace(".", "").replace(",", "").isnumeric()
                        )
                    ).quantize(Decimal(".0001"), rounding=ROUND_DOWN)
                except ValueError:
                    raise InvalidStyleValue

            self.swag_bank.payer_a_cagnotte(message.author.id, cagnotte_idx, value)

            cagnotte_name = (
                self.swag_bank.get_active_cagnotte(cagnotte_idx).get_info().name
            )
            await message.channel.send(
                "Transaction effectuée avec succès ! \n"
                "```ini\n"
                f"[{message.author.display_name}\t"
                f"{format_number(value)} {currency}\t"
                f"-->\t€{cagnotte_idx} {cagnotte_name}]\n"
                "```"
            )
            await update_forbes_classement(message.guild, self, self.client)

        elif "donner" in splited_command:
            cagnotte_idx = get_cagnotte_idx_from_command(splited_command)

            destinataire = message.mentions
            if len(destinataire) != 1:
                await message.channel.send(
                    "Merci de mentionner un destinataire (@Bobby Machin) pour "
                    "lui donner une partie de cette €agnotte !"
                )
                return
            destinataire = destinataire[0]

            currency = (
                self.swag_bank.get_active_cagnotte(cagnotte_idx).get_info().currency
            )

            if currency == "$wag":
                try:
                    value = int(
                        "".join(
                            argent for argent in splited_command if argent.isnumeric()
                        )
                    )
                except ValueError:
                    raise InvalidSwagValue

            elif currency == "$tyle":
                try:
                    value = Decimal(
                        "".join(
                            argent
                            for argent in splited_command
                            if argent.replace(".", "").replace(",", "").isnumeric()
                        )
                    ).quantize(Decimal(".0001"), rounding=ROUND_DOWN)
                except ValueError:
                    raise InvalidStyleValue

            self.swag_bank.donner_depuis_cagnotte(
                cagnotte_idx, destinataire.id, value, message.author.id
            )

            cagnotte_name = (
                self.swag_bank.get_active_cagnotte(cagnotte_idx).get_info().name
            )
            await message.channel.send(
                "Transaction effectuée avec succès ! \n"
                "```ini\n"
                f"[€{cagnotte_idx} {cagnotte_name}\t"
                f"{format_number(value)} {currency}\t"
                f"-->\t{destinataire.display_name}]\n"
                "```"
            )

            await update_forbes_classement(message.guild, self, self.client)

        elif "partager" in splited_command:
            cagnotte_idx = get_cagnotte_idx_from_command(splited_command)
            cagnotte_currency = (
                self.swag_bank.get_active_cagnotte(cagnotte_idx).get_info().currency
            )
            cagnotte_name = self.swag_bank.get_cagnotte_info(cagnotte_idx).name
            participants_id = [participant.id for participant in message.mentions]

            (
                participants_id,
                gain,
                gagnant_miette,
                miette,
            ) = self.swag_bank.partage_cagnotte(
                cagnotte_idx, participants_id, message.author.id
            )

            participants_str = []
            for participant_id in participants_id:
                user = message.guild.get_member(participant_id)
                if user == None:
                    participants_str.append(
                        await get_guild_member_name(
                            participant_id, message.guild, self.client
                        )
                    )
                else:
                    participants_str.append(user.mention)

            participants_mention = ", ".join(participants_str)

            await message.channel.send(
                f"{participants_mention} vous avez chacun récupéré `{gain} {cagnotte_currency}`"
                f" de la cagnotte **{cagnotte_name}** 💸"
            )

            if gagnant_miette != None:
                user = message.guild.get_member(gagnant_miette)
                if user == None:
                    user_gagnant = await get_guild_member_name(
                        gagnant_miette, message.guild, self.client
                    )
                else:
                    user_gagnant = user.mention
                await message.channel.send(
                    f"{user_gagnant} récupère les `{miette} {cagnotte_currency}` restants ! 🤑"
                )

            await update_forbes_classement(message.guild, self, self.client)

        elif "loto" in splited_command:
            cagnotte_idx = get_cagnotte_idx_from_command(splited_command)
            participants_id = [participant.id for participant in message.mentions]

            gagnant, gain = self.swag_bank.tirage_au_sort_cagnotte(
                cagnotte_idx, participants_id, message.author.id
            )

            cagnotte_currency = (
                self.swag_bank.get_active_cagnotte(cagnotte_idx).get_info().currency
            )
            cagnotte_name = (
                self.swag_bank.get_active_cagnotte(cagnotte_idx).get_info().name
            )

            await message.channel.send(
                f"{message.guild.get_member(gagnant).mention} vient de gagner l'intégralité de la €agnotte "
                f"€{cagnotte_idx} *{cagnotte_name}*, à savoir `{gain} {cagnotte_currency}` ! 🎰"
            )

            await update_forbes_classement(message.guild, self, self.client)

        elif "détruire" in splited_command:
            cagnotte_idx = get_cagnotte_idx_from_command(splited_command)
            cagnotte_name = (
                self.swag_bank.get_active_cagnotte(cagnotte_idx).get_info().name
            )

            self.swag_bank.detruire_cagnotte(cagnotte_idx, message.author.id)
            await message.channel.send(
                f"La €agnotte €{cagnotte_idx} *{cagnotte_name}* est maintenant détruite de ce plan de l'existence ❌"
            )
            await update_forbes_classement(message.guild, self, self.client)

        else:
            await message.channel.send(
                f"{message.author.mention}, tu as l'air perdu "
                "(c'est un peu normal, avec ces commandes pétées du cul...) 🙄\nVoici les commandes "
                "que tu peux utiliser avec les €agnottes :\n"
                "```HTTP\n"
                "!€agnotte créer [$wag/$tyle] [Nom_de_la_€agnotte] ~~ "
                "Permet de créer une nouvelle €agnotte, de $wag ou de $tyle "
                "avec le nom de son choix\n"
                "!€agnotte info €[n] ~~ Affiche des informations détaillés sur la €agnotte n\n"
                "!€agnotte historique €[n] ~~ Affiche les transactions en lien avec la €agnotte n\n"
                "!€agnotte payer €[n] [montant] ~~ fait don "
                "de la somme choisi à la €agnotte numéro €n\n"
                "⭐!€agnotte donner €[n] [montant] [@mention] ~~ donne à l'utilisateur mentionné "
                "un montant venant de la cagnotte\n"
                "⭐!€agnotte partager €[n] [@mention1 @mention2 ...] ~~ "
                "Partage l'intégralité de la €agnotte entre les utilisateurs mentionné. "
                "Si personne n'est mentionné, la €agnotte sera redistribué parmis ses donateurs\n"
                "⭐!€agnotte loto €[n] [@mention1 @mention2 ...] ~~ "
                "Tire au sort parmis les utilisateurs mentionnés celui qui remportera l'intégralité "
                "de la €agnotte. Si personne n'est mentionné, le tirage au sort se fait parmis"
                "l'ensemble des personnes ayant un compte\n"
                "⭐!€agnotte détruire €[n] ~~ Détruit la €agnotte si elle est vide"
                "```\n"
                "*Seul le gestionnaire de la €agnotte peut faire les commandes précédées d'une  ⭐*"
            )
