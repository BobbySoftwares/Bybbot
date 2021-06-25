from glob import glob
from enum import Enum, auto
import os.path
import re
from random import choice


def clear_string(s):
    """Nettoie un string de tout un tas de caractères, enlève les
    accents à des lettres, et transforme toutes les majuscules en
    minuscule.

    Args:
        s (String): String à nettoyer

    Returns:
        String: String nettoyé
    """
    clean_s = ""
    s = s.lower()
    clean_s = (
        s.replace("\n", "")
        .replace("\r", "")
        .replace(", ", " ")
        .replace(",", "")
        .replace("é", "e")
        .replace("è", "e")
        .replace("à", "a")
        .replace("â", "a")
        .replace("û", "u")
        .replace("ô", "o")
        .replace("ç", "c")
        .replace("ï", "i")
        .replace(" ", "_")
        .replace("\u00A0", "_")
        .replace('"', "")
        .replace("'", "")
        .replace("*", "")
        .replace("|", "")
    )
    return clean_s


def clear_all_string(lst):
    """Permet d'utiliser la fonction clear_string dans l'ensemble de
    string dans une liste

    Args:
        lst (list): Liste de String

    Returns:
        List: Liste de String nettoyé
    """
    return [clear_string(s) for s in lst]


def deep_is_inside(s, lst_string):
    """Permet de voir si une chaîne de caractère est inclut dans une
    des chaînes de caractères d'une liste de string

    Args:
        s (String): chaîne de caractère à trouver
        lst_string (List): Liste de chaîne de caractère

    Returns:
        Bool: True si s est au moins dans une des chaînes de caractères
            de lst_string, False sinon.
    """
    return any(s in string for string in lst_string)


def attr_to_tags_and_transcription(attr):
    """Permet de récupérer les tags et la transcription écrit dans les
    attributs d'une commande pour lancer un son

    Args:
        attr (str): Attribut d'une commande de son lancé par un
            utilisateur

    Returns:
        (List[str], str): tableau de tags et transcription en str
    """
    tags = []
    recherche = ""

    # Je fais un for each si jamais il y en a en plusieurs en mode
    # [Humain][Arthas]
    for tag in re.findall(" *\\[.*?\\] *", attr):
        tag_without_bracket = tag[tag.find("[") + 1 : tag.find("]")]
        tags = tags + tag_without_bracket.replace(", ", ",").replace(" ,", ",").split(
            ","
        )
        attr = attr.replace(tag, "")  # Enlève les tags des attributs

    recherche = attr
    return tags, recherche


class CodeRecherche(Enum):
    """Énumérateur utilisé pour indiqué si la recherche de son à donné
    aucun résultat, 1 seul résultat, plusieurs résultats, trop de
    résultats, ou si l'utilisateur a demandé de l'aide
    """

    NO_RESULT = auto()
    ONE_RESULT = auto()
    SOME_RESULT = auto()
    TOO_MANY_RESULT = auto()
    REQUEST_HELP = auto()


class Son:
    """Un Son est composé de plusieurs tags ainsi que d'une
    transcription, avec ces informations, il est facile d'en trouver
    le chemin
    """

    def __init__(self, lst_tags, trans):
        self.tags = lst_tags.copy()
        self.transcription = trans

    def __repr__(self):
        if not self.tags:
            return f"Aucun Tags : {self.transcription}"
        else:
            return f"Tags : {self.tags} {self.transcription}"

    def __str__(self):
        if not self.tags:
            return f"(Aucun Tags)\t{self.transcription}"
        else:
            return f"{self.tags}\t{self.transcription}"

    def get_path_of_sound(self, sound_file_path, command):
        """Permet de récupérer le chemin du fichier contenant le son
        correspondant

        Args:
            sound_file_path (String): Dossier qui contient tout les
                sons (par défaut sounds)
            command (String): la commande utilisé (aoe, war3, kaa...)

        Returns:
            String: Chemin relatif du son à lancer
        """
        sound_number = self.transcription.split("-")[
            0
        ]  # le numéro est toujours la première chose avant le -
        if not self.tags:
            return glob(f"{sound_file_path}/{command}/{sound_number}-*")[0]
        else:
            return glob(
                f"{sound_file_path}/{command}/{'/'.join(self.tags)}"
                f"/{sound_number}-*"
            )[0]


class Jukebox:
    """Représentation abstraite de l'ensemble des sons à rechercher et
    à jouer
    """

    def __init__(self, sound_file="."):
        self.dico_jukebox = {}
        self.sound_file_path = sound_file
        for folder_path in glob(f"{sound_file}/*"):

            # Récupération du nom du fichier
            folder_name = os.path.basename(folder_path)

            # Génération de la liste des transcriptions
            transcription_file_lst = glob(f"{folder_path}/**/*.tr", recursive=True)

            sound_tab = []
            for transcription_file in transcription_file_lst:

                # Récupération des tags
                tags_lst = os.path.dirname(
                    transcription_file
                )  # retourne le chemin sans le fichier transcription au bout
                tags_lst = tags_lst.replace("\\", "/").split(
                    "/"
                )  # On remplace les \\ par / pour Windows.
                tags_lst = tags_lst[
                    2:
                ]  # exclut le fichier sounds et le fichier war3 ou aoe.

                # Récupération de chaque ligne du fichier transcription
                with open(transcription_file, "r", encoding="utf-8") as f:
                    transcription_lines = f.readlines()

                # Création du tableau des sons :
                for transcription in transcription_lines:
                    sound_tab.append(Son(tags_lst, transcription.replace("\n", "")))

            self.dico_jukebox[folder_name] = sound_tab

        # Liste des commandes dont le jukebox pourra être appelé (exemple (!aoe,!war3))
        self.command_tuple = tuple(
            [f"!{command} " for command in list(self.dico_jukebox.keys())]
        )
        print(self.dico_jukebox.keys())

    def search_with_the_command(self, command, attr):
        """Lance la recherche de son à partir d'une commande utilisateur

        Args:
            command (String): aoe, kaa, war3 ...
            attr (String): attribut donné à la commande (que la lumière
                soit avec nous, OU, [Uther] que la lumière soit avec nous)

        Returns:
            file_path (String): Chemin du Son qui a été trouvé (None si
                non trouvé)
            search_result (List[Son]) : Ensemble des sons qui
                correspondent à la recherche
            search_code_success (CodeRecherche) : Code indiquant une
                information concernant la requête de l'utilisateur
        """
        tags, recherche = attr_to_tags_and_transcription(attr)

        search_result = self.search_for_sounds(command, tags, recherche)

        # Gestion des différents cas de figures

        # 1er cas le résultat est vide
        if not search_result:
            file_path = None
            search_code_success = CodeRecherche.NO_RESULT

        elif "help" in attr:
            file_path = None
            search_code_success = CodeRecherche.REQUEST_HELP

        # 2nd cas, le résultat présente plusieurs possibilité
        elif len(search_result) > 1 and len(search_result) <= 15:
            file_path = None
            search_code_success = CodeRecherche.SOME_RESULT

        elif len(search_result) > 15:
            file_path = None
            search_code_success = CodeRecherche.TOO_MANY_RESULT

        else:
            file_path = search_result[0].get_path_of_sound(
                self.sound_file_path, command
            )
            search_code_success = CodeRecherche.ONE_RESULT

        return file_path, search_result, search_code_success

    def search_for_sounds(self, command, tags, recherche):
        """Retourne la liste des sons qui corresponde au tag et à la recherche

        Args:
            command (String): aoe, war3, kaa, etc...
            tags (Liste): liste de tag en format String
            recherche (String): la recherche utilisateur

        Returns:
            List: Liste des sons compatible avec la recherche
        """
        sounds_tab = self.dico_jukebox.get(command)

        # Tags filtering, si le tableau n'est pas vide
        if tags:
            result = [
                sound
                for sound in sounds_tab
                if all(
                    deep_is_inside(clear_string(tag), clear_all_string(sound.tags))
                    for tag in tags
                )
            ]
        else:
            result = sounds_tab

        splitrecherche = recherche.split(" ")

        # Cas particulier : Si recherche = random
        if clear_string(recherche) == "random" and result:
            return [choice(result)]

        # Cas particulier : Si recherche = help ou si il contient le mot help
        if clear_string(recherche) == "help" and result:
            return result
        elif "help" in splitrecherche:
            splitrecherche.remove("help")

        # Cas particulier : si la recherche contient un nombre seulement
        if recherche.isnumeric():
            return [
                sound
                for sound in result
                if sound.transcription.startswith(f"{recherche}-")
            ]

        # Calcul des résulats
        final_result = [
            sound
            for sound in result
            if all(
                [
                    clear_string(subrecherche) in clear_string(sound.transcription)
                    for subrecherche in splitrecherche
                ]
            )
        ]

        # check if final_result is not the same sound but different version, in that
        # case, play a random sound.
        if final_result:
            if final_result[0].transcription[-1].isnumeric():
                intermediate = []
                for r in final_result:
                    intermediate.append(r.transcription.split("-", 1)[1][:-1])

                if len(set(intermediate)) == 1:
                    final_result = [choice(final_result)]
        ##

        return final_result

    def jukebox_stat(self):
        """Envoie différente statistique du jukebox (Quels sont les
        ommandes disponibles, et combien chaque commande a de sons à
        disposition)

        Returns:
            String: Information concernant le jukebox
        """
        return "\n".join(
            f"{len(lst)} son(s) trouvé(s) pour la commande `!{key}`."
            for key, lst in self.dico_jukebox.items()
        )
