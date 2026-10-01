"""
app.py
------
Application Flask du cabinet.

Pages disponibles :
    /patients     -> liste des patients
    /rendez-vous  -> liste des rendez-vous, avec le nom du patient concerné

Pour la lancer (depuis la racine du projet, avec (venv) actif) :
    python3 app.py
"""

import sqlite3
from flask import Flask

app = Flask(__name__)


def se_connecter_a_la_base():
    connexion = sqlite3.connect("database/cabinet.db")
    connexion.row_factory = sqlite3.Row
    return connexion


@app.route("/patients")
def liste_patients():
    connexion = se_connecter_a_la_base()
    curseur = connexion.cursor()

    curseur.execute("SELECT * FROM patients ORDER BY nom")
    patients = curseur.fetchall()

    connexion.close()

    html = "<h1>Liste des patients</h1><ul>"
    for patient in patients:
        html += f"<li>{patient['prenom']} {patient['nom']} — né(e) le {patient['date_naissance']}</li>"
    html += "</ul>"

    return html


@app.route("/rendez-vous")
def liste_rendez_vous():
    connexion = se_connecter_a_la_base()
    curseur = connexion.cursor()

    # JOINTURE : on relie la table "rendez_vous" à la table "patients"
    # grâce à la colonne commune patient_id (côté rendez_vous) = id (côté patients).
    #
    # "r" et "p" sont des surnoms (alias) qu'on donne aux tables pour écrire
    # moins de texte : r.date_rdv au lieu de rendez_vous.date_rdv, par exemple.
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

    return html


if __name__ == "__main__":
    app.run(debug=True)
