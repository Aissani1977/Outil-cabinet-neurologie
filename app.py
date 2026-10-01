"""
app.py
------
Première application Flask du cabinet.
Pour l'instant, elle fait une seule chose : afficher la liste des patients
enregistrés dans cabinet.db, dans le navigateur.

Pour la lancer (depuis la racine du projet, avec (venv) actif) :
    python3 app.py

Puis ouvrir dans le navigateur : http://localhost:5000/patients
"""

import sqlite3
from flask import Flask

# 1. On crée l'application Flask.
#    "__name__" dit à Flask où se trouve ce fichier, pour qu'il puisse
#    ensuite retrouver d'autres fichiers du projet (templates, images...).
app = Flask(__name__)


# 2. Une petite fonction utilitaire pour se connecter à la base.
#    On la réutilisera dans toutes les pages qui ont besoin des données.
def se_connecter_a_la_base():
    # Le chemin pointe vers le fichier cabinet.db, qui est dans le dossier "database"
    connexion = sqlite3.connect("database/cabinet.db")
    # Cette ligne permet de récupérer les résultats sous forme de dictionnaires
    # (avec les noms de colonnes) plutôt que de simples listes de valeurs.
    connexion.row_factory = sqlite3.Row
    return connexion


# 3. Une "route" : elle dit à Flask "quand quelqu'un visite cette adresse,
#    exécute cette fonction et renvoie ce qu'elle produit".
@app.route("/patients")
def liste_patients():
    connexion = se_connecter_a_la_base()
    curseur = connexion.cursor()

    # On récupère tous les patients, triés par nom
    curseur.execute("SELECT * FROM patients ORDER BY nom")
    patients = curseur.fetchall()

    connexion.close()

    # 4. On construit une page HTML très simple, ligne par ligne.
    #    (Ce n'est pas encore joli, on améliorera avec de vrais templates
    #    dans une prochaine étape — pour l'instant on vérifie que ça marche.)
    html = "<h1>Liste des patients</h1><ul>"
    for patient in patients:
        html += f"<li>{patient['prenom']} {patient['nom']} — né(e) le {patient['date_naissance']}</li>"
    html += "</ul>"

    return html


# 5. Ce bloc ne s'exécute que si on lance directement "python3 app.py"
#    (et pas si ce fichier est importé depuis un autre script).
if __name__ == "__main__":
    # debug=True affiche les erreurs détaillées dans le navigateur, très
    # utile pendant l'apprentissage. On désactivera ça avant la mise en ligne réelle.
    app.run(debug=True)
