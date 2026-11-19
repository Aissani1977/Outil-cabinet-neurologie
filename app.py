"""
app.py
------
Application Flask du cabinet.

Pages disponibles (accessibles depuis le menu à gauche) :
    /patients      -> liste des patients (cliquer sur un nom ouvre sa fiche)
    /patients/<id> -> fiche d'un patient, avec ses onglets
    /consultations -> tableau récapitulatif des consultations
    /rendez-vous   -> liste des rendez-vous, avec le nom du patient concerné
    /comptes-rendus -> comptes-rendus de consultation détaillés

Pour la lancer (depuis la racine du projet, avec (venv) actif) :
    python3 app.py
"""

import sqlite3
from datetime import date
from html import escape
from flask import Flask, request, abort

app = Flask(__name__)


def se_connecter_a_la_base():
    connexion = sqlite3.connect("database/cabinet.db")
    connexion.row_factory = sqlite3.Row
    return connexion


# Les liens du menu de gauche : (adresse de la page, texte affiché).
# Pour ajouter une page au menu, il suffit d'ajouter une ligne ici.
MENU = [
    ("/patients", "Patients"),
    ("/consultations", "Consultations"),
    ("/rendez-vous", "Rendez-vous"),
    ("/comptes-rendus", "Comptes rendus"),
]


def mise_en_page(contenu):
    """
    Entoure le contenu d'une page avec la mise en page commune :
    l'en-tête en haut, le menu à gauche, la zone principale à droite
    et le pied de page en bas.
    Chaque route appelle cette fonction au lieu de renvoyer son HTML directement.
    """
    liens = ""
    for adresse, texte in MENU:
        # On met en évidence le lien de la page actuellement affichée
        # (ou d'une de ses sous-pages, ex : /patients/3 allume "Patients").
        if request.path == adresse or request.path.startswith(adresse + "/"):
            classe = "actif"
        else:
            classe = ""
        liens += f"<a href='{adresse}' class='{classe}'>{texte}</a>"

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <title>Cabinet médical de Neurologie Dr Aissani.N</title>
    <style>
        body {{ margin: 0; font-family: sans-serif; display: flex; flex-direction: column; min-height: 100vh; }}
        header {{ background: #1f2d3a; color: white; padding: 18px 30px; }}
        header h1 {{ margin: 0; font-size: 22px; }}
        .milieu {{ flex: 1; display: flex; }}
        nav {{ width: 200px; background: #2c3e50; padding-top: 20px; flex-shrink: 0; }}
        nav a {{ display: block; color: #ecf0f1; text-decoration: none; padding: 12px 20px; }}
        nav a:hover {{ background: #34495e; }}
        nav a.actif {{ background: #1abc9c; }}
        main {{ flex: 1; padding: 20px 40px; }}
        footer {{ background: #1f2d3a; color: #ecf0f1; text-align: center; padding: 12px; }}
        table {{ border-collapse: collapse; }}
        th, td {{ border: 1px solid #ccc; padding: 6px 12px; text-align: left; }}
        .recherche {{ display: flex; gap: 10px; align-items: center; margin-bottom: 20px; flex-wrap: wrap; }}
        .recherche input {{ padding: 6px 8px; min-width: 200px; }}
        .fiche-nom {{ font-size: 30px; font-weight: bold; margin-top: 10px; }}
        .fiche-details {{ font-size: 15px; color: #666; margin: 4px 0 20px 0; }}
        .cadre {{ border: 1px solid #ccc; border-radius: 6px; }}
        .onglets {{ display: flex; border-bottom: 1px solid #ccc; background: #f5f5f5; border-radius: 6px 6px 0 0; }}
        .onglets a {{ padding: 12px 20px; text-decoration: none; color: #2c3e50; }}
        .onglets a:hover {{ background: #e8e8e8; }}
        .onglets a.actif {{ background: white; border-bottom: 3px solid #1abc9c; font-weight: bold; }}
        .contenu-onglet {{ padding: 20px; }}
    </style>
</head>
<body>
    <header>
        <h1>Cabinet médical de Neurologie Dr Aissani.N</h1>
    </header>
    <div class="milieu">
        <nav>
            {liens}
        </nav>
        <main>
            {contenu}
        </main>
    </div>
    <footer>
        DR. Nawel AISSANI - Neurologue
    </footer>
</body>
</html>"""


@app.route("/patients")
def liste_patients():
    # Critères saisis dans le formulaire de recherche (vides = pas de filtre).
    recherche_nom = request.args.get("nom", "").strip()
    recherche_naissance = request.args.get("naissance", "").strip()
    recherche_tel = request.args.get("telephone", "").strip()

    # On construit la requête seulement avec les critères remplis.
    # Les valeurs passent par "?" (paramètres), jamais collées dans le SQL.
    conditions = []
    parametres = []
    if recherche_nom:
        # Le texte peut correspondre au nom OU au prénom.
        conditions.append("(nom LIKE ? OR prenom LIKE ?)")
        motif = f"%{recherche_nom}%"
        parametres += [motif, motif]
    if recherche_naissance:
        conditions.append("date_naissance = ?")
        parametres.append(recherche_naissance)
    if recherche_tel:
        conditions.append("telephone LIKE ?")
        parametres.append(f"%{recherche_tel}%")

    requete = "SELECT * FROM patients"
    if conditions:
        requete += " WHERE " + " AND ".join(conditions)
    requete += " ORDER BY nom"

    connexion = se_connecter_a_la_base()
    curseur = connexion.cursor()

    curseur.execute(requete, parametres)
    patients = curseur.fetchall()

    connexion.close()

    # Formulaire de recherche : trois critères côte à côte.
    # Les valeurs saisies sont remises dans les champs (escape protège le HTML).
    html = f"""
        <h1>Liste des patients</h1>
        <form method='get' action='/patients' class='recherche'>
            <input type='text' name='nom' placeholder='Nom ou prénom' value='{escape(recherche_nom)}'>
            <input type='date' name='naissance' title='Date de naissance' value='{escape(recherche_naissance)}'>
            <input type='text' name='telephone' placeholder='Téléphone' value='{escape(recherche_tel)}'>
            <button type='submit'>Rechercher</button>
            <a href='/patients'>Effacer</a>
        </form>
    """

    if not patients:
        html += "<p>Aucun patient ne correspond à la recherche.</p>"

    html += "<ul>"
    for patient in patients:
        # Chaque nom est un lien vers la fiche du patient.
        html += (
            f"<li><a href='/patients/{patient['id']}'>{patient['prenom']} {patient['nom']}</a>"
            f" — né(e) le {patient['date_naissance']}</li>"
        )
    html += "</ul>"

    return mise_en_page(html)


# Les onglets de la fiche patient : (nom utilisé dans l'adresse, texte affiché).
ONGLETS_PATIENT = [
    ("infos", "Informations personnelles"),
    ("consultations", "Consultations"),
    ("documents", "Documents"),
    ("rendez-vous", "Rendez-vous"),
]

SEXES = {"M": "Homme", "F": "Femme"}


def calculer_age(date_naissance):
    """Calcule l'âge à partir d'une date au format AAAA-MM-JJ."""
    if not date_naissance:
        return "Âge non renseigné"
    naissance = date.fromisoformat(date_naissance)
    aujourd_hui = date.today()
    age = aujourd_hui.year - naissance.year
    # Si l'anniversaire n'est pas encore passé cette année, on retire 1 an.
    if (aujourd_hui.month, aujourd_hui.day) < (naissance.month, naissance.day):
        age -= 1
    return f"{age} ans"


@app.route("/patients/<int:patient_id>")
def fiche_patient(patient_id):
    # L'onglet affiché est choisi dans l'adresse : /patients/3?onglet=documents
    # Sans précision, on affiche les informations personnelles.
    onglet = request.args.get("onglet", "infos")

    connexion = se_connecter_a_la_base()
    curseur = connexion.cursor()

    curseur.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    patient = curseur.fetchone()
    if patient is None:
        connexion.close()
        abort(404)  # Aucun patient avec cet identifiant : page "introuvable".

    # --- Contenu de l'onglet choisi ---
    if onglet == "consultations":
        curseur.execute(
            "SELECT * FROM consultations WHERE patient_id = ? ORDER BY date_consultation DESC",
            (patient_id,),
        )
        consultations = curseur.fetchall()
        contenu = ""
        for c in consultations:
            contenu += f"<h3>{c['date_consultation']} — {c['motif']}</h3>"
            contenu += f"<p><strong>Observations :</strong> {c['observations']}</p>"
            contenu += f"<p><strong>Diagnostic :</strong> {c['diagnostic']}</p>"
            contenu += f"<p><strong>Traitement :</strong> {c['traitement']}</p>"
            contenu += f"<p><strong>Médecin :</strong> {c['medecin']}</p>"
        if not consultations:
            contenu = "<p>Aucune consultation enregistrée.</p>"

    elif onglet == "documents":
        curseur.execute(
            "SELECT * FROM documents WHERE patient_id = ? ORDER BY date_document DESC",
            (patient_id,),
        )
        documents = curseur.fetchall()
        contenu = "<table><tr><th>Date</th><th>Type</th><th>Titre</th><th>Fichier</th></tr>"
        for d in documents:
            contenu += (
                f"<tr><td>{d['date_document']}</td><td>{d['type_document']}</td>"
                f"<td>{d['titre']}</td><td>{d['nom_fichier']}</td></tr>"
            )
        contenu += "</table>"
        if not documents:
            contenu = "<p>Aucun document enregistré.</p>"

    elif onglet == "rendez-vous":
        curseur.execute(
            "SELECT * FROM rendez_vous WHERE patient_id = ? ORDER BY date_rdv DESC, heure_rdv DESC",
            (patient_id,),
        )
        rendez_vous = curseur.fetchall()
        contenu = "<table><tr><th>Date</th><th>Heure</th><th>Motif</th><th>Statut</th></tr>"
        for rdv in rendez_vous:
            contenu += (
                f"<tr><td>{rdv['date_rdv']}</td><td>{rdv['heure_rdv']}</td>"
                f"<td>{rdv['motif']}</td><td>{rdv['statut']}</td></tr>"
            )
        contenu += "</table>"
        if not rendez_vous:
            contenu = "<p>Aucun rendez-vous enregistré.</p>"

    else:
        onglet = "infos"  # Onglet inconnu dans l'adresse : on revient aux infos.
        contenu = f"""
            <h3>Date de naissance</h3>
            <p>{patient['date_naissance']}</p>
            <h3>Coordonnées</h3>
            <p><strong>Téléphone :</strong> {patient['telephone']}</p>
            <p><strong>Email :</strong> {patient['email']}</p>
            <p><strong>Adresse :</strong> {patient['adresse']}</p>
            <h3>Antécédents</h3>
            <p>{patient['antecedents']}</p>
        """

    connexion.close()

    # --- Barre des onglets (l'onglet affiché est mis en évidence) ---
    liens_onglets = ""
    for cle, texte in ONGLETS_PATIENT:
        classe = "actif" if cle == onglet else ""
        liens_onglets += f"<a href='/patients/{patient_id}?onglet={cle}' class='{classe}'>{texte}</a>"

    # --- Assemblage de la fiche ---
    sexe = SEXES.get(patient["sexe"], "Sexe non renseigné")
    html = f"<div class='fiche-nom'>{patient['nom'].upper()} {patient['prenom']}</div>"
    html += f"<div class='fiche-details'>{calculer_age(patient['date_naissance'])} · {sexe}</div>"
    html += "<div class='cadre'>"
    html += f"<div class='onglets'>{liens_onglets}</div>"
    html += f"<div class='contenu-onglet'>{contenu}</div>"
    html += "</div>"

    return mise_en_page(html)


@app.route("/rendez-vous")
def liste_rendez_vous():
    connexion = se_connecter_a_la_base()
    curseur = connexion.cursor()

    curseur.execute("""
        SELECT
            r.date_rdv,
            r.heure_rdv,
            r.motif,
            r.statut,
            p.nom,
            p.prenom
        FROM rendez_vous AS r
        JOIN patients AS p ON r.patient_id = p.id
        ORDER BY r.date_rdv, r.heure_rdv
    """)
    rendez_vous = curseur.fetchall()

    connexion.close()

    html = "<h1>Liste des rendez-vous</h1><ul>"
    for rdv in rendez_vous:
        html += (
            f"<li>{rdv['date_rdv']} à {rdv['heure_rdv']} — "
            f"{rdv['prenom']} {rdv['nom']} — {rdv['motif']} "
            f"<em>({rdv['statut']})</em></li>"
        )
    html += "</ul>"

    return mise_en_page(html)


@app.route("/consultations")
def liste_consultations():
    # Vue courte : une ligne par consultation, dans un tableau.
    connexion = se_connecter_a_la_base()
    curseur = connexion.cursor()

    curseur.execute("""
        SELECT
            c.date_consultation,
            c.motif,
            c.diagnostic,
            c.medecin,
            p.nom,
            p.prenom
        FROM consultations AS c
        JOIN patients AS p ON c.patient_id = p.id
        ORDER BY c.date_consultation
    """)
    consultations = curseur.fetchall()

    connexion.close()

    html = "<h1>Consultations</h1>"
    html += "<table><tr><th>Date</th><th>Patient</th><th>Motif</th><th>Diagnostic</th><th>Médecin</th></tr>"
    for c in consultations:
        html += (
            f"<tr><td>{c['date_consultation']}</td>"
            f"<td>{c['prenom']} {c['nom']}</td>"
            f"<td>{c['motif']}</td>"
            f"<td>{c['diagnostic']}</td>"
            f"<td>{c['medecin']}</td></tr>"
        )
    html += "</table>"

    return mise_en_page(html)


@app.route("/comptes-rendus")
def liste_comptes_rendus():
    # Vue détaillée : le compte-rendu complet de chaque consultation.
    connexion = se_connecter_a_la_base()
    curseur = connexion.cursor()

    # Même principe de jointure que pour les rendez-vous : on relie
    # "consultations" à "patients" via consultations.patient_id = patients.id
    curseur.execute("""
        SELECT
            c.date_consultation,
            c.motif,
            c.observations,
            c.diagnostic,
            c.traitement,
            c.medecin,
            p.nom,
            p.prenom
        FROM consultations AS c
        JOIN patients AS p ON c.patient_id = p.id
        ORDER BY c.date_consultation
    """)
    consultations = curseur.fetchall()

    connexion.close()

    # Ici on affiche un peu plus d'informations par consultation,
    # donc on construit un petit bloc par compte-rendu plutôt qu'une simple ligne.
    html = "<h1>Comptes-rendus de consultation</h1>"
    for c in consultations:
        html += "<div style='margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #ccc;'>"
        html += f"<h3>{c['prenom']} {c['nom']} — {c['date_consultation']}</h3>"
        html += f"<p><strong>Motif :</strong> {c['motif']}</p>"
        html += f"<p><strong>Observations :</strong> {c['observations']}</p>"
        html += f"<p><strong>Diagnostic :</strong> {c['diagnostic']}</p>"
        html += f"<p><strong>Traitement :</strong> {c['traitement']}</p>"
        html += f"<p><strong>Médecin :</strong> {c['medecin']}</p>"
        html += "</div>"

    return mise_en_page(html)


if __name__ == "__main__":
    app.run(debug=True)
