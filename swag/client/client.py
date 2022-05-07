import disnake
from disnake.ext import commands
from swag.client.cagnotte import CagnotteCommand
from swag.client.swag import SwagCommand
from swag.client.swagdmin import execute_swagdmin_command
from swag.blockchain import SyncedSwagChain
from swag.client.yfu import YfuCommand
from swag.errors import (
    CagnotteNameAlreadyExist,
    CagnotteDestructionForbidden,
    CagnotteUnspecifiedException,
    NoCagnotteAccountRegistered,
    NotEnoughMoneyInCagnotte,
    NotCagnotteManager,
)
from apscheduler.triggers.cron import CronTrigger
from arrow import utcnow

import traceback

from swag.id import UserId

from ..errors import (
    AlreadyCagnotteManager,
    AlreadyMineToday,
    InvalidCagnotteId,
    InvalidSwagValue,
    InvalidStyleValue,
    InvalidTimeZone,
    NoReceiver,
    OrphanCagnotte,
    TimeZoneFieldLocked,
    NoSwagAccountRegistered,
    AccountAlreadyExist,
    NotEnoughStyleInBalance,
    NotEnoughSwagInBalance,
    StyleStillBlocked,
)
from ..utils import (
    update_forbes_classement,
    update_the_style,
)

from utils import (
    ADMINS_ID,
    GUILD_ID,
    LOG_CHANNEL_ID,
    SWAGCHAIN_CHANNEL_ID,
)
from module import Module


class SwagClient(Module):
    def __init__(self, discord_client) -> None:
        self.discord_client = discord_client
        print("Initialisation de la $wagChain...\n")
        self.guilds = {}
        self.the_swaggest = None
        self.last_update = None
        self.last_backup = None

    def register_commands(self):
        
        self.discord_client.add_cog(SwagCommand(self))
        self.discord_client.add_cog(CagnotteCommand(self))
        self.discord_client.add_cog(YfuCommand(self))
        self.discord_client.add_cog(ClientError())

    async def setup(self):
        self.swagchain = await SyncedSwagChain.from_channel(
            self.discord_client.user.id,
            self.discord_client.get_channel(SWAGCHAIN_CHANNEL_ID),
        )
        print("Mise à jour du classement et des bonus de blocage\n\n")
        await update_forbes_classement(
            self.discord_client.get_guild(GUILD_ID),
            self,
            self.discord_client,
        )

    async def add_jobs(self, scheduler):
        # Programme la fonction update_the_style pour être lancée
        # toutes les heures.
        async def style_job():
            now = utcnow().replace(microsecond=0, second=0, minute=0)
            if self.last_update is None or self.last_update < now:
                self.last_update = now
                await update_the_style(self.discord_client, self)

        async def backup_job():
            now = utcnow().replace(microsecond=0, second=0, minute=0)
            if self.last_backup is None or self.last_backup < now:
                self.last_backup = now
                await self.swagchain.save_backup()

        #Génération du style toute les heures
        scheduler.add_job(style_job, CronTrigger(hour="*"))
        #Sauvegarde de la swagchain en local tout les jours à 4h du matin 
        scheduler.add_job(backup_job, CronTrigger(day="*", hour="4"))

    async def process(self, message):
        try:
            if message.content.startswith("!$wagdmin"):
                await execute_swagdmin_command(self, message)
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


##TODO : Possible amélioration
## Créer un ClientCommand qui sera un Cog qui importera les autres Cog (Swag, Style, Yfu, Swagadmin...)


class ClientError(commands.Cog):
    """
    Cog qui écoute les erreurs envoyées par les slash commands et envoie le bon message d'erreur associé
    """

    ##TODO check the source
    @commands.Cog.listener()
    async def on_slash_command_error(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        error: commands.CommandInvokeError,
    ):

        if type(error.original) is AccountAlreadyExist:
            await interaction.response.send_message(
                f"⚠️ {interaction.author.mention}, tu possèdes déjà un compte sur la $wagChain™ !",
                ephemeral=True,
            )

        elif type(error.original) is NotEnoughSwagInBalance:
            await interaction.response.send_message(
                f"{interaction.author.mention} ! Tu ne possèdes pas assez de $wag pour faire cette transaction, "
                "vérifie ton solde avec `!$wag solde`",
                ephemeral=True,
            )

        elif type(error.original) is InvalidSwagValue:
            await interaction.response.send_message(
                f"{interaction.author.mention}, la valeur que tu as écrite est "
                "incorrecte, elle doit être supérieur à 0 et entière, car le "
                "$wag est **indivisible** !",
                ephemeral=True,
            )
        elif type(error.original) is AlreadyMineToday:
            await interaction.response.send_message(
                f"Désolé {interaction.author.mention}, mais tu as déjà miné du $wag "
                "aujourd'hui 😮 ! Reviens donc demain !",
                ephemeral=True,
            )
        elif type(error.original) is StyleStillBlocked:
            await interaction.response.send_message(
                f"{interaction.author.mention}, du $wag est déjà bloqué à ton compte "
                "chez $tyle Generator Inc. ! Attends leurs déblocage pour pouvoir "
                "en bloquer de nouveau !",
                ephemeral=True,
            )
        elif type(error.original) is NotEnoughStyleInBalance:
            await interaction.response.send_message(
                f"{interaction.author.mention} ! Tu ne possèdes pas assez de $tyle "
                "pour faire cette transaction, vérifie ton solde avec "
                "`!$tyle solde`",
                ephemeral=True,
            )
        elif type(error.original) is InvalidStyleValue:
            await interaction.response.send_message(
                f"{interaction.author.mention}, la valeur que tu as écrite est "
                "incorrecte, elle doit être supérieur à 0, car le $tyle est "
                "**toujours positif** !",
                ephemeral=True,
            )
        elif type(error.original) is NoSwagAccountRegistered:
            await interaction.response.send_message(
                f"{error.original.name}, tu ne possèdes pas de compte sur la $wagChain™ "
                "<:rip:817165391846703114> !\n\n"
                "Remédie à ce problème en lançant la commande `!$wag créer` "
                "et devient véritablement $wag 😎!",
                ephemeral=True,
            )
        elif type(error.original) is AccountAlreadyExist:
            await interaction.response.send_message(
                f"{interaction.author.mention}, tu possèdes déjà un compte sur la $wagChain™ !",
                ephemeral=True,
            )
        elif type(error.original) is InvalidTimeZone:
            await interaction.response.send_message(
                f"{error.original.name}, n'est pas un nom de timezone valide !\n"
                "Vérifie le nom correct sur "
                "https://en.wikipedia.org/wiki/List_of_tz_database_time_zones, "
                "à la colone `TZ database name`.",
                ephemeral=True,
            )
        elif type(error.original) is TimeZoneFieldLocked:
            await interaction.response.send_message(
                "Tu viens déjà de changer de timezone. Tu ne pourras effectuer "
                f"à nouveau cette opération qu'après le {error.original.date}. Cette mesure "
                "vise à empécher l'abus de minage, merci de ta compréhension.\n\n"
                "*L'abus de minage est dangereux pour la santé. À Miner avec "
                "modération. Ceci était un message de la Fédération Bobbyique du "
                "Minage*",
                ephemeral=True,
            )
        elif type(error.original) is InvalidCagnotteId:
            await interaction.response.send_message(
                f"L'id **{error.original.value}** que tu as donné est invalide ! "
                f"Un id correct commence par **'€'** et ne contenir que des caractères du type **[a-zA-Z0-9_]**.",
                ephemeral=True,
            )
        elif type(error.original) is NoCagnotteAccountRegistered:
            await interaction.response.send_message(
                f"Aucune €agnotte n°€{error.original.name} est active sur la $wagChain ! "
                f"{interaction.author.mention}, tu t'es sans doute trompé de numéro 🤨",
                ephemeral=True,
            )
        elif type(error.original) is CagnotteNameAlreadyExist:
            await interaction.response.send_message(
                f"{interaction.author.mention}, une €agnotte porte déjà ce nom ! "
                "Je te conseille de choisir un autre nom avant que tout le monde "
                "soit complètement duper 🤦‍♂️",
                ephemeral=True,
            )
        elif type(error.original) is NotEnoughMoneyInCagnotte:
            await interaction.response.send_message(
                f"{interaction.author.mention}, tu es en train de demander à la €agnotte {error.original.id} "
                "une somme d'argent qu'elle n'a pas. Non mais tu n'as pas honte ? 😐",
                ephemeral=True,
            )
        elif type(error.original) is NotCagnotteManager:
            await interaction.response.send_message(
                f"{error.original.name} ne fais pas partie des gestionnaires "
                "de cette €agnotte. Impossible de faire cette action.",
                ephemeral=True,
            )
        elif type(error.original) is AlreadyCagnotteManager:
            await interaction.response.send_message(
                f"{error.original.name} fait déjà partie des gestionnaires de cette €agnotte.",
                ephemeral=True,
            )
        elif type(error.original) is OrphanCagnotte:
            await interaction.response.send_message(
                f"Une €agnotte doit avoir **au moins un** gestionnaire.",
                ephemeral=True,
            )
        elif type(error.original) is CagnotteDestructionForbidden:
            await interaction.response.send_message(
                f"**Ligne 340 des conditions générales d'utilisations des €agnottes :**\n\n"
                "*Il est formellement interdit de détruire une cagnotte qui n'est pas vidée "
                "de son contenu. C'est comme ça.*",
                ephemeral=True,
            )
        elif type(error.original) is CagnotteUnspecifiedException:
            await interaction.response.send_message(
                f"{interaction.author.mention}, il manque l'identifiant de la €agnotte"
                " dans la commande (€3 par exemple) afin de pouvoir faire l'action que tu demandes.",
                ephemeral=True,
            )
        elif type(error.original) is NoReceiver:
            await interaction.response.send_message(
                f"{interaction.author.mention}, merci de mentionner un destinataire"
                "(@Bobby Machin) !",
                ephemeral=True,
            )
        elif type(error.original) is AttributeError and hasattr(error.original,"name") and error.original.name == "swagchain":
                await interaction.response.send_message(
                    f"{interaction.author.mention}, la $wagChain n'est pas encore disponible. "
                    "Veuillez réessayer d'ici quelques secondes !",
                    ephemeral=True,
                )
        else:
            try:
                admins_id = [str(UserId(admin_id)) for admin_id in ADMINS_ID]

                await interaction.client.get_channel(LOG_CHANNEL_ID).send(
                    f"{', '.join(admins_id)} ! "
                    "Une erreur inattendue est "
                    f"survenue suite à la commande de {interaction.author.mention} :\n\n"
                    f"`/{interaction.data.name} {interaction.options}`\n\n"
                    "L'erreur est la suivante :\n"
                    "```\n"
                    f"{''.join(traceback.format_tb(error.original.__traceback__))}\n"
                    f"{error.original}\n"
                    "```"
                )
                await interaction.response.send_message(
                    f"{interaction.author.mention} ! ***Une erreur inattendue est survenue.*** "
                    "Les développeurs viennent d'en être informés. Merci de bien vouloir "
                    "patienter... ⌛"
                )
            except:
                traceback.print_tb(error.original.__traceback__)
                print(f"{error.original}")
