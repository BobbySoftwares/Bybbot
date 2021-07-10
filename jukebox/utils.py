def well_aligned_jukebox_tab(lst_sound, prefix="", suffix=""):
    """Affiche sur plusieurs lignes les informations (numéro, [tag],
    transcription) associées à la liste de sons spécifiée.

    Fait partie de la fonctionnalité jukebox.

    Args:
        lst_sound (List[jukebox.Son]): Liste des sons à afficher
        prefix (str): Caractère préfixant chaque ligne (utile pour
            utiliser les couleurs)
        suffix (str): Caractère suffixant chaque ligne

    Returns:
        str : La chaîne de caractère à afficher
    """
    # TODO: Check if replace("'", "") is needed
    # TODO: Remove need for this list
    tags = [str(sound.tags).replace("'", "") for sound in lst_sound]

    # Détermination de la chaîne de caractère la plus longue pour les tags
    width = max(len(tag) for tag in tags)

    if width > 2:
        return "\n".join(
            f"{prefix}{tag : <{width}} || {sound.transcription}{suffix}"
            for sound, tag in zip(lst_sound, tags)
        )
    else:  # Si il n'y a que des sons sans aucun tag dans le tableau
        return "\n".join(
            f"{prefix}{sound.transcription}{suffix}" for sound in lst_sound
        )


def mini_help_message_string(
    sub_soundlst, current_page, nbr_pages, message_user=None, client=None
):
    """Fonction utilisé par la fonctionnalité du Jukebox
    Appelée lorsqu'on veut afficher un message d'aide pour l'affichage
    du catalogue est son disponible en fonction de la commande

    Args:
        sub_soundlst (lst): sous-liste de son
        current_page (int): La page courante, utilisé pour l'afficher
            en bas du message
        nbr_pages (int): Le nombre de page total, utilisé pour
            l'afficher en bas du message
        message_user ([type], optional): Ce paramètre n'a aucune
            incidence ici. Defaults to None.

    Returns:
        String: Une chaîne de caractère correspondant à un message
            d'aide pour le jukebox
    """
    return (
        "Voici ce que j'ai en stock <:cozmo:774656738469216287>.\n"
        "Tu dois choisir judicieusement <:ris:800855908859117648> !\n"
        "```fix\n"
        f"{well_aligned_jukebox_tab(sub_soundlst)}\n"
        f"Page {current_page}/{nbr_pages}\n```"
    )
