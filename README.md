# Rush 2 · Analyse des ventes d'une pharmacie

Projet du MBA Data Epitech (promo 2028), groupe **Les 3 M** : Manon Desclaux, Manon Rollet et Mina.

Une pharmacie indépendante a exporté ses ventes de janvier 2014 à octobre 2019 pour 8 groupes de médicaments (codes
ATC), en quantités et sans prix. Le manager pose deux questions :

1. **Peut-on prévoir les ventes du mois suivant ?** Oui pour 3 groupes sur 8 (M01AB, M01AE, N02BE, soit 64 % des
   volumes), R06 sous réserve. Pour les autres, reprendre les ventes du mois précédent suffit ou les ventes sont trop
   irrégulières. Le test porte sur 33 mois de prévision à origine glissante, comparée à la méthode « le mois prochain =
   le mois dernier ».
2. **Peut-on partager l'export avec un laboratoire ?** Oui, sous conditions : au jour ou à l'heure, une vente
   d'hypnotique correspond à une personne (donnée de santé, RGPD art. 9). Au mois, ce risque disparaît. Le partage
   demande aussi un contrat écrit, une remise indépendante de l'accès aux données et une validation juridique.

Les résultats sont détaillés dans la [note de synthèse](livrables/Note_de_synthese_finale.pdf).

## Contenu

| Dossier | Rôle |
|---|---|
| `livrables/` | Note de synthèse (PDF), audit du classeur, et les trois présentations : manager, pharmacien, propriétaire |
| `code/` | `analyse.py` (contrôles croisés des exports, statistiques, saisonnalité, test de prévision, lien avec la grippe) et `charts.py` (graphiques). `results.json` contient les chiffres cités dans la note et les présentations |
| `data/` | Les quatre exports de ventes (horaire, journalier, hebdomadaire, mensuel), le classeur `Pharmacie_Analyse 2.xlsx` et le classeur `Classeur3.xlsx` utilisé par le notebook |
| `notebook/` | Notebook d'exploration : qualité des données, jours fériés, saisonnalité, météo |

## Rejouer l'analyse

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python code/analyse.py data "data/Pharmacie_Analyse 2.xlsx" code/externe/sentinelles_grippe_hebdo_france.csv outputs
python code/charts.py outputs
```

`analyse.py` vérifie que l'onglet Historique du classeur est identique à l'export journalier, refait les contrôles
croisés entre exports (l'export mensuel est écarté : 45 cellules sur 560 ne concordent pas), puis écrit
`outputs/results.json`.

## Sources

- Ventes : export de la pharmacie, 2014-2019.
- Grippe : Réseau Sentinelles (Inserm, Sorbonne Université), indicateur 3, France, téléchargé le 12/10/2026 depuis
  https://www.sentiweb.fr/datasets/all/inc-3-PAY.csv.
- Température : Météo-France ; pollens : RNSA (capteur de Montpellier) ; jours fériés : calendrier.api.gouv.fr.
