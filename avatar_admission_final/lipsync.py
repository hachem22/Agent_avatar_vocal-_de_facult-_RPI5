# lipsync.py
# ---------------------------------------------------------
# Calcule un "timeline" d'ouverture/fermeture de bouche base
# sur le TEXTE (mots/syllabes) plutot que sur le volume brut.
# Resultat : la bouche bouge en rythme avec ce qui est dit,
# avec une vraie fermeture entre les mots.
# ---------------------------------------------------------

VOYELLES = "aeiouyàâäéèêëîïôöùûü"


def compter_syllabes(mot: str) -> int:
    """Estimation grossiere du nombre de syllabes d'un mot francais."""
    mot = mot.lower()
    count = 0
    voyelle_precedente = False
    for ch in mot:
        est_voyelle = ch in VOYELLES
        if est_voyelle and not voyelle_precedente:
            count += 1
        voyelle_precedente = est_voyelle
    return max(1, count)


def construire_timeline(texte: str, duree_totale: float, silence_entre_mots: float = 0.06):
    """
    Retourne une liste de segments (debut, fin, intensite) ou intensite
    est un flottant entre 0 (bouche fermee) et 1 (bouche grande ouverte).
    """
    mots = texte.split()
    if not mots or duree_totale <= 0:
        return []

    syllabes_par_mot = [compter_syllabes(m) for m in mots]
    total_syllabes = sum(syllabes_par_mot) or len(mots)

    temps_silences = silence_entre_mots * max(0, len(mots) - 1)
    temps_parole = max(0.05, duree_totale - temps_silences)

    timeline = []
    t = 0.0

    for mot, nb_syllabes in zip(mots, syllabes_par_mot):
        duree_mot = temps_parole * (nb_syllabes / total_syllabes)
        duree_segment = duree_mot / (2 * nb_syllabes)  # alterne ouvert/ferme par syllabe

        for _ in range(nb_syllabes):
            timeline.append((t, t + duree_segment, 1.0))       # bouche ouverte
            t += duree_segment
            timeline.append((t, t + duree_segment, 0.35))      # legere fermeture (transition)
            t += duree_segment

        # silence entre les mots : bouche fermee
        timeline.append((t, t + silence_entre_mots, 0.0))
        t += silence_entre_mots

    return timeline


def intensite_a_instant(timeline, instant: float) -> float:
    """Retourne l'intensite (0 a 1) de la bouche a un instant donne du timeline."""
    if not timeline:
        return 0.0
    for debut, fin, intensite in timeline:
        if debut <= instant < fin:
            return intensite
    return 0.0  # apres la fin du timeline : bouche fermee
