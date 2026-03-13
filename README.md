# Taxe Héritage : Modèle de microsimulation fiscale

Ce dépôt contient le code source et la documentation méthodologique du modèle de microsimulation conçu pour le projet de recherche : *"Distinguer le mérite de l'héritage : Enjeux et limites d'une fiscalité duale des successions en France"*.

## Description du projet
Ce modèle permet de simuler les impacts budgétaires et redistributifs d'une réforme fiscale distinguant le **capital créé** (issu de l'effort d'épargne) du **capital hérité** (issu de la reproduction patrimoniale). 

L'outil repose sur une architecture de flux stationnaires et intègre des variables de mortalité différentielle pour refléter la réalité des inégalités sociales face à la transmission.

## Accès au simulateur
Vous pouvez tester le modèle en temps réel via l'interface interactive :
👉 [https://taxe-heritage1.streamlit.app/](https://taxe-heritage1.streamlit.app/)

## Structure du dépôt
- `app.py` : Script principal utilisant le framework *Streamlit* pour l'interface et le moteur de calcul.
- `requirements.txt` : Liste des bibliothèques Python nécessaires pour exécuter le modèle localement.
- `README.md` : Documentation du projet.

## Utilisation locale
Pour exécuter le modèle sur votre machine :

1. Clonez le dépôt :
   `git clone https://github.com/emilegippa0/taxe-heritage1.git`
2. Installez les dépendances :
   `pip install -r requirements.txt`
3. Lancez l'application :
   `streamlit run app.py`

## Licence
Ce projet est mis à disposition sous licence MIT, favorisant la transparence et la reproductibilité des travaux de recherche.

---
*Projet de recherche réalisé dans le cadre d'un cursus en économie.*
