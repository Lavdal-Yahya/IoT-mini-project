# Mouhamedou Yahya Cheikh Med Vall
# 25239
# Maryeim Mohamed T'Feil
# 22087

# Présentation analytique, version dashboard-design

Le fichier [diagnostic_dashboard.pptx](diagnostic_dashboard.pptx) contient dix diapositives modifiables, avec notes orales estimées à **600 secondes**. Il constitue une autre version du support existant. La répétition humaine chronométrée reste à faire.

Cette variante applique la compétence `dashboard-design` demandée : le périmètre et la population précèdent les résultats, les barres E1–E4 partagent une échelle de 0 à 100 %, et E4 conserve la même couleur d’accent. Les gains sont exprimés en points avec leur référence. La matrice distingue les comptes bruts de fenêtres et la métrique pondérée par essai. Les effectifs, l’essai sain unique et les intervalles restent visibles.

Le diaporama est un support explicatif, sans filtres ni données simulées. Il présente le même test final gelé. Les tableaux et les deux graphiques de scores sont des objets natifs éditables. Les figures de signaux sont incorporées au fichier. Aucun signal n’a été réanalysé pour modifier un score.

Depuis le 21 novembre 2026, cette version reprend le thème clair de la présentation web : fond blanc, ink-black `#000814`, prussian-blue `#001d3d`, regal-navy `#003566`, school-bus-yellow `#ffc300` et gold `#ffd60a`. Les barres E4 et la cellule E4 de l'ablation sont dorées ; la matrice utilise des cellules bleu marine et des erreurs sur fond jaune pâle. Les deux figures sont retracées depuis les valeurs enregistrées de la version web, avec les mêmes couleurs de classes et des symboles distincts.

## Déroulé de dix minutes

| Diapositive | Sujet | Durée estimée |
| ---: | --- | ---: |
| 1 | Diagnostic et question de transfert | 35 s |
| 2 | Effectifs par classe et charge | 60 s |
| 3 | Trois indicateurs temporels | 55 s |
| 4 | BPFO, BPFI et enveloppe | 70 s |
| 5 | Préparation, fenêtre et résolution | 55 s |
| 6 | Ablation des entrées et du modèle | 55 s |
| 7 | Choix du développement | 75 s |
| 8 | Transfert final à 3 HP | 80 s |
| 9 | Erreurs et agrégation par essai | 65 s |
| 10 | Incertitude et limites | 50 s |

Les quinze questions préparées dans [questions_reponses.md](../questions_reponses.md) restent applicables. Les sources propres à chaque diapositive sont dans ses notes.

## Régénérer le fichier

Le constructeur [build_dashboard.mjs](build_dashboard.mjs) lit directement `results/summary.csv`, `results/final_metrics.json`, `results/final_bootstrap.json`, `results/selection.json`, `configs/experiment.json` et `data/classcoverage.csv`. Avant l'export, `.venv/bin/python presentation/dashboard/build_theme_figures.py` retrace les deux figures sous `assets/` depuis `presentation/web/dist/data.js`. Les scripts n’entraînent aucun modèle.

[export_dashboard.mjs](export_dashboard.mjs) utilise le runtime Node et `@oai/artifact-tool` fournis par Codex, ainsi que le validateur de la compétence Presentations. Renseigner les chemins du runtime renvoyés par `load_workspace_dependencies` :

```sh
export ARTIFACT_NODE_MODULES=/chemin/du/runtime/node_modules
export ARTIFACT_PYTHON=/chemin/du/runtime/python3
export PRESENTATIONS_SKILL=/chemin/de/la/competence/presentations
/chemin/du/runtime/node presentation/dashboard/export_dashboard.mjs presentation/dashboard/diagnostic_dashboard_revision.pptx
```

Le générateur refuse d’écraser un fichier final existant. Un dossier temporaire unique `tmp/dashboard-build-*/` contient les rendus de contrôle et la validation. Il reste hors Git. Après validation d'une révision, recopier le fichier final à l'emplacement du livrable pour le mettre à jour. Les classeurs incorporés dans les graphiques sont des instantanés des valeurs publiées, sans formules scientifiques. La reconstruction du support est indépendante de la reproduction scientifique Python.

La variante est livrée en PowerPoint séparé car la session de présentation du chat est liée au support initial et la création d’un second artefact n’est pas disponible. Le support initial conserve son contenu et son identifiant. Le fichier a été rendu et contrôlé, puis importé par Artifact Tool ; aucune ouverture dans Microsoft PowerPoint n’est revendiquée.
