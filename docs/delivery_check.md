# Mouhamedou Yahya Cheikh Med Vall
# 25239
# Maryeim Mohamed T'Feil
# 22087

# Contrôle de livraison du mini-projet AML313 — groupe 7

Contrôle documentaire du 20 novembre 2026. Cette fiche relie le sujet 7 (p. 10) et le barème (p. 12) aux preuves présentes. Elle ne remplace pas l'état des jalons dans `ROADMAP.md` ni la checklist `tasks.md`.

## Cinq tâches du sujet 7

| Tâche | Preuve vérifiable | État |
| --- | --- | --- |
| 1. RMS, kurtosis, facteur de crête ; comparaison sain/défectueux | `src/bearing_diagnosis/features.py`, `tests/test_features.py`, `results/figures/temporal_features.png`, § 2 de `report/rapport.pdf` | Réalisée. Les points de la figure sont des médianes par enregistrement du développement. |
| 2. BPFO/BPFI et spectre d'enveloppe | `src/bearing_diagnosis/signals.py`, `results/figures/spectra_envelope.png`, `results/feature_dictionary.csv`, § 3 de l'article | Réalisée. Les deux vitesses saines approximatives et la bande fixe 2–5 kHz sont signalées comme limites. |
| 3. Résolution FFT et fenêtre | `configs/experiment.json`, `docs/features.md`, `tests/test_signals.py`, § 3 de l'article | Réalisée. Fenêtre brute de 1 s : 12 000 points à 12 kHz et espacement 1 Hz ; enveloppe de 0,9 s : environ 1,111 Hz. |
| 4. Baseline, modèle riche et ablation | `results/selection.json`, `results/development_oof.csv`, `results/development_metrics.json`, `results/summary.csv`, § 4 de l'article | Réalisée. E1 est l'arbre à trois variables ; E2–E4 changent un facteur à la fois. E4 a été choisi sur le développement avant le test. |
| 5. Généralisation à une autre charge | `data/splits/recordings.csv`, `results/freeze.json`, `results/test_consulted.json`, `results/final_predictions.csv`, `results/final_metrics.json`, § 5 de l'article | Réalisée pour la charge réservée 3 HP. Ce résultat ne prouve pas un transfert vers une autre machine. |

## Grille d'évaluation (20 points)

| Critère du barème | Points | Preuve et réserve |
| --- | ---: | --- |
| Diagnostic des données : grille, manquants, doublons, mécanisme | 3 | `data/manifest.csv`, `data/audit.json`, `data/classcoverage.csv`, `docs/data_audit.md`. Quarante fichiers contrôlés ; deux vitesses MAT manquantes sont tracées, sans valeur mesurée inventée. |
| Préparation journalisée et caractéristiques causales | 3 | `results/preparation_development.json`, `results/preparation_final_test.json`, `results/filter_diagnostics.json`, `src/bearing_diagnosis/signals.py`, `docs/features.md`. Le diagnostic d'une fenêtre n'est disponible qu'à sa fin. |
| Baseline correcte pour la tâche | 3 | E1 : RMS, kurtosis, facteur de crête et arbre. `results/selection.json` et `results/summary.csv`. |
| Modèle plus riche, ablation, choix justifiés | 3 | E1–E4 dans `results/summary.csv` ; choix E4 avant le test dans `docs/development_decision.md` ; figures `results/figures/development_scores.png` et `results/figures/ablation.png`. Les scores de développement après sélection sont optimistes. |
| Validation sans fuite ; test unique | 4 | `data/splits/split_plan.json` : validation par charge entière ; `results/freeze.json` et `results/test_consulted.json` ; garde-fous `tests/test_protocol.py`. L'identité des roulements physiques entre essais n'est pas documentée. |
| Métriques, incertitude, décision métier | 2 | `results/development_metrics.json`, `results/final_metrics.json`, `results/final_bootstrap.json`, `results/figures/final_confusion.png` et `results/figures/final_window_confusion.png`. Un seul essai sain à 3 HP limite l'intervalle de variabilité entre essais. |
| Reproductibilité, article, soutenance | 2 | `results/clean_clone_verification.json` : 368 prédictions finales identiques depuis un clone propre et un environnement verrouillé ; `report/rapport.pdf` : six pages ; `presentation/plan_soutenance.md`, `presentation/questions_reponses.md`, `presentation/slides.md` : préparation de l'oral. La répétition humaine chronométrée reste à faire. |

## Contrôle des chiffres et de la frontière finale

L'article reprend `results/summary.csv` : 30 essais et 268 fenêtres de développement, puis 10 essais et 92 fenêtres finales. E4 a 99,69 % d'exactitude équilibrée pondérée hors pli et 98,15 % sur 3 HP. E1 atteint 90,74 % sur 3 HP. E4 classe correctement les dix essais agrégés, mais son rappel pondéré des fenêtres de bague externe vaut 92,59 % ; ces deux mesures ne se contredisent pas. Le bootstrap final donne E4 - E1 = +7,41 points, intervalle percentile 95 % [0 ; 17,59] points. La borne basse n'établit pas un gain strict.

Les chemins de code vérifiés maintiennent la séparation : `splits.py` attribue chaque charge à un pli entier ; `models.py` n'utilise que `BASE_FEATURES` ou `FULL_FEATURES` pour X et rejette les colonnes de métadonnées ; `cli.py` vérifie le gel et écrit le marqueur avant l'extraction finale. `final_test` reprend la sélection gelée et ne choisit pas de modèle avec les scores de 3 HP. La reproduction compare les prédictions aux références publiées sans refaire la recherche de grille.

## À terminer avant de déclarer M6 clos

- [ ] Effectuer une répétition **humaine** chronométrée de 10 minutes et vérifier la préparation aux 5 minutes de questions (T49). Les dix diapositives modifiables et les fiches sont prêtes ; leur existence ne prouve pas l’entraînement oral.
- [x] Vérifier le jeu de dix diapositives final et les fichiers choisis pour publication (T51). Toutes les pages et diapositives ont été rendues et inspectées ; tableaux et graphiques restent modifiables.
- [x] Versionner et publier la livraison, puis contrôler l’état du dépôt distant (T52). Le commit `5d7e8f5` est poussé sur `origin/main` ; empreinte distante et HEAD concordent.

La référence [1] de l'article renvoie directement aux deux tables CWRU utilisées pour le sous-ensemble. Les URL de chaque fichier figurent dans `data/manifest.csv`.

## Variante analytique du support

`presentation/dashboard/diagnostic_dashboard.pptx` propose dix diapositives supplémentaires en tant que version alternative du même oral. Les cinq tâches du sujet, la sélection avant le test, l’ablation, les erreurs et les limites y sont reprises. Dix rendus ont été inspectés. Le fichier passe les contrôles de structure, dimensions, polices, tableaux et graphiques natifs, ainsi que l’import Artifact Tool. Aucun essai scientifique supplémentaire ni répétition humaine n’a été effectué.
