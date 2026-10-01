"""
app.py
------
Application Flask du cabinet.

Pages disponibles :
    /patients      -> liste des patients
    /rendez-vous   -> liste des rendez-vous, avec le nom du patient concerné
    /consultations -> liste des comptes-rendus de consultation

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


@app.route("/consultations")
def liste_consultations():
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

    return html


if __name__ == "__main__":
    app.run(debug=True)
