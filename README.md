# Mouhamedou Yahya Cheikh Med Vall
# 25239

# AML313 — Mini-projet du groupe 7

## Sujet

Diagnostiquer un défaut de roulement par analyse vibratoire à partir des données CWRU.

Dépôt : [Lavdal-Yahya/IoT-mini-project](https://github.com/Lavdal-Yahya/IoT-mini-project).

## Documents de référence

| Document | Rôle |
| --- | --- |
| [ROADMAP.md](ROADMAP.md) | Source de vérité pour l'objectif, le périmètre, les étapes, les jalons et l'avancement. |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Source de vérité pour les choix techniques, les interfaces et la validation. |
| [tasks.md](tasks.md) | Checklist ordonnée des actions et preuves, rattachées aux jalons de la roadmap. |
| [Mini-projet-AML313.pdf](Mini-projet-AML313.pdf) | Cadre commun page 3, sujet 7 page 10, barème page 12. |
| [AGENTS.md](AGENTS.md) | Instructions pour maintenir le code et les documents cohérents. |

Les décisions et l'état des jalons restent dans la roadmap et l'architecture ; `tasks.md` détaille leur exécution. Le README ne duplique pas leur suivi. Les instructions explicites de l'utilisateur priment ; l'énoncé reste la référence pédagogique. Toute adaptation est documentée.

## Démarrage

Lire la roadmap, puis l'architecture et la checklist. Le pipeline scientifique et ses résultats sont disponibles. L'avancement détaillé reste dans ces documents.

## Installer et reproduire

Python **3.12** est requis. L'environnement vérifié utilise Python 3.12.14. Depuis la racine du dépôt :

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python -m pip install -e . --no-deps
make reproduce
```

`make reproduce` vérifie ou télécharge les 40 fichiers MAT officiels, refait l'audit et les partitions, reconstruit les caractéristiques et réentraîne les réglages déjà gelés. Il compare les 368 prédictions finales (quatre modèles × 92 fenêtres) aux références publiées. Il ne choisit pas de nouveaux paramètres. Une connexion réseau est nécessaire pour les sources officielles, y compris leur inventaire.

```sh
make test
```

Les données brutes (~134 Mo), les environnements et les modèles générés restent hors Git. Le manifeste permet de vérifier les sources par SHA-256. Les conditions de redistribution des signaux ne sont pas établies ; le dépôt contient les liens et les empreintes.

## Résultats et documents scientifiques

- [Tableau des résultats](results/summary.csv), [sélection avant le test](results/selection.json) et [gel scientifique](results/freeze.json).
- [Audit des données](docs/data_audit.md), [protocole](docs/protocol.md), [caractéristiques](docs/features.md) et [décision de développement](docs/development_decision.md).
- Figures dans [results/figures](results/figures/) ; prédictions et métriques détaillées dans [results](results/).
- [Article de six pages](report/rapport.pdf) et source de génération dans [report](report/) ; [support modifiable et storyboard](presentation/README.md), notes et questions dans [presentation](presentation/).

Les scores principaux sont pondérés pour donner le même poids à chaque enregistrement. Le diagnostic agrégé par essai et les scores bruts par fenêtre sont aussi conservés. Un seul enregistrement sain est disponible à 3 HP ; les résultats ne prouvent pas une généralisation à d'autres machines.

## Étapes du pipeline

```sh
make audit       # acquisition et audit
make extract     # caractéristiques du développement seulement
make develop     # recherche bornée et ablation sur le développement
make freeze      # empreintes du protocole avant le test
make evaluate    # campagne finale, refusée si le test a déjà été consulté
make report      # figures et tables à partir d'une exécution complète
```

Ces commandes décrivent l'expérience d'origine. Le test publié est déjà consulté : utiliser `make reproduce` pour le rejouer à l'identique. Une nouvelle variante après lecture des résultats est exploratoire et demande une nouvelle évaluation indépendante pour être confirmée.

## Références pédagogiques locales

Ces ressources restent dans le workspace pédagogique parent. Elles ne sont pas incluses dans ce dépôt ; les chemins suivants sont locaux au workspace d'origine.

- `../cours/01_Fondations_et_bruit_dans_les_flux_IIoT.pdf` : échantillonnage et bruit.
- `../cours/03_Caracteristiques_et_analyse_statistique.pdf` : indicateurs vibratoires, FFT et enveloppe.
- `../cours/05_Validation_stricte_et_mini_projet.pdf` : validation, incertitude et reproductibilité.
- `../TP/tp1/` : qualité des données et agrégation RMS.
- `../TP/tp3/` : interprétation physique et limites expérimentales.

## Reconstruire le PDF de l’article

Le PDF est déjà livré. Sa reconstruction éditoriale utilise ReportLab 4.4.9, pypdf 6.21.4 et les polices Liberation du système (voir `report/build_report.py`). Ces outils de mise en page sont séparés de l’environnement scientifique gelé. Dans un environnement dédié contenant ces deux paquets :

```sh
python report/build_report.py
```

Le générateur lit les preuves sous `results/` et exige exactement six pages. Après toute modification éditoriale, rendre et vérifier les six pages ; ne pas relancer une recherche scientifique sur le test final pour modifier l’article.
