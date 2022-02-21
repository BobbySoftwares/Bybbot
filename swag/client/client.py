from swag.client.cagnotte import execute_cagnotte_command
from swag.client.style import execute_style_command
from swag.client.swagdmin import execute_swagdmin_command
from swag.blockchain import SyncedSwagChain
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

from ..errors import (
    AlreadyMineToday,
    InvalidSwagValue,
    InvalidStyleValue,
    InvalidTimeZone,
    NoReceiver,
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
    GUILD_ID,
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

        scheduler.add_job(style_job, CronTrigger(hour="*"))

    async def process(self, message):
        try:
            if message.content.startswith("!$wagdmin"):
                await execute_swagdmin_command(self, message)
#            elif message.content.startswith("!$wag"):
#                await execute_swag_command(self, message)
            elif message.content.startswith("!$tyle"):
                await execute_style_command(self, message)
            elif message.content.startswith("!€agnotte"):
                await execute_cagnotte_command(self, message)
#            elif message.content.startswith("!Yfu"):
#                await execute_yfu_command(self, message)
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
        except NoSwagAccountRegistered as e:
            await message.channel.send(
                f"{e.name}, tu ne possèdes pas de compte sur la $wagChain™ "
                "<:rip:817165391846703114> !\n\n"
                "Remédie à ce problème en lançant la commande `!$wag créer` "
                "et devient véritablement $wag 😎!"
            )
        except AccountAlreadyExist:
            await message.channel.send(
                f"{message.author.mention}, tu possèdes déjà un compte sur la $wagChain™ !"
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
        except NoCagnotteAccountRegistered as e:
            await message.channel.send(
                f"Aucune €agnotte n°€{e.name} est active sur la $wagChain ! "
                f"{message.author.mention}, tu t'es sans doute trompé de numéro 🤨"
            )
        except CagnotteNameAlreadyExist:
            await message.channel.send(
                f"{message.author.mention}, une €agnotte porte déjà ce nom ! "
                "Je te conseille de choisir un autre nom avant que tout le monde "
                "soit complètement duper 🤦‍♂️"
            )
        except NotEnoughMoneyInCagnotte as e:
            await message.channel.send(
                f"{message.author.mention}, tu es en train de demander à la €agnotte {e.id} "
                "une somme d'argent qu'elle n'a pas. Non mais tu n'as pas honte ? 😐"
            )
        except NotCagnotteManager:
            await message.channel.send(
                f"{message.author.mention}, tu ne fais pas partie des gestionnaires "
                "de cette €agnotte, tu ne peux donc pas manipuler son contenu 🤷‍♀️"
            )
        except CagnotteDestructionForbidden:
            await message.channel.send(
                f"**Ligne 340 des conditions générales d'utilisations des €agnottes :**\n\n"
                "*Il est formellement interdit de détruire une cagnotte qui n'est pas vidée "
                "de son contenu. C'est comme ça.*"
            )
        except CagnotteUnspecifiedException:
            await message.channel.send(
                f"{message.author.mention}, il manque l'identifiant de la €agnotte"
                " dans la commande (€3 par exemple) afin de pouvoir faire l'action que tu demandes."
            )
        except NoReceiver:
            await message.channel.send(
                f"{message.author.mention}, merci de mentionner un destinataire"
                "(@Bobby Machin) !"
            )
        except AttributeError as e:
            if e.name == "swagchain":
                await message.channel.send(
                    f"{message.author.mention}, la $wagChain n'est pas encore disponible. "
                    "Veuillez réessayer d'ici quelques secondes !"
                )
            else:
                raise
