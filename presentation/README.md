# Mouhamedou Yahya Cheikh Med Vall
# 25239
# Maryeim Mohamed T'Feil
# 22087

# Support de soutenance

Le diaporama Spaces associé au projet contient dix diapositives. Le [storyboard](slides.md) donne les messages, chiffres, sources et durées estimées. Les [notes orales](plan_soutenance.md) et les [questions et réponses](questions_reponses.md) complètent le support. Une répétition humaine chronométrée reste à faire.

La figure agrandie `envelope_examples.png` se régénère à partir de deux essais du **développement** avec :

```bash
PYTHONPATH=src .venv/bin/python presentation/build_envelope_figures.py
```

Le script vérifie `split_role = development`, reprend la préparation fixée dans `configs/experiment.json`, et n'entraîne aucun modèle. Les données finales ne servent pas à cette figure.

`build_slides.mjs` décrit les objets modifiables du diaporama. Son callback `build` s'exécute dans une session `artifact_session` connectée, en quatre appels séquentiels avec `input.phase` égal à `cover`, `a`, `b`, puis `c`. Chaque appel reçoit `input.root`, chemin absolu du dépôt. Les phases `b` et `c` reçoivent aussi `input.scores`, produit par `loadScores(input.root)` à partir de `results/summary.csv`. Les graphiques E1–E4 sont natifs. La matrice d'erreurs et les tableaux sont natifs. Les figures temporelles et d'enveloppe restent des images de résultats, avec leurs données d'origine conservées.

Les résultats présentés viennent de `results/summary.csv`, `results/final_metrics.json` et `results/final_bootstrap.json`. Le diaporama est une présentation du banc CWRU étudié. Les limites de l’essai sain unique au test final et de la dépendance physique possible entre charges figurent sur la dernière diapositive. Les deux vitesses approximatives sont signalées dans les notes de la diapositive 2.

## Accéder au support et le reconstruire

Le support modifiable est fourni dans le chat Codex ayant produit le projet. [artifact.json](artifact.json) conserve l’identifiant exact de session, sans URL publique ni Page ID retourné. Le storyboard et le callback restent versionnés pour reconstruire le support dans une nouvelle session.

```javascript
var root = '/chemin/absolu/IoT-mini-project';
var builder = await import(root + '/presentation/build_slides.mjs');
var scores = await builder.loadScores(root);
```

Exécuter ensuite `builder.default` dans quatre appels `artifactSession.run` séparés avec `input: {root, scores, phase}`, et le même `artifactRef`. La phase `cover` attend la première diapositive vide d’une nouvelle session ; chacune des phases suivantes ajoute trois diapositives. Rendre et inspecter les dix diapositives après reconstruction.

## Autre version analytique

La [version dashboard-design](dashboard/README.md) est un diaporama PowerPoint distinct de dix diapositives. Elle conserve les mêmes résultats et auteurs avec des comparaisons alignées, une matrice de confusion et des limites visibles. Les notes sont estimées à dix minutes, sans répétition humaine revendiquée.

## Version web interactive

La [présentation web Apache ECharts](web/README.md) propose dix diapositives, un mode plein écran, des notes et des graphiques interactifs. Elle conserve les mêmes auteurs et le protocole gelé. Les instructions locales, la publication et les limites de vérification sont dans ce dossier.
