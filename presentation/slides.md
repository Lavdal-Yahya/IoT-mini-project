# Mouhamedou Yahya Cheikh Med Vall
# 25239

# Storyboard du diaporama AML313 — groupe 7

Ce storyboard décrit dix diapositives construites dans la présentation Spaces liée au projet. Le minutage est **une estimation de 10 minutes**, sans répétition humaine chronométrée. Les chiffres et matrices proviennent des sorties vérifiées sous `results/`. Les graphiques de scores et les tableaux sont des éléments natifs modifiables ; les figures de signal restent des images scientifiques existantes.

| Nº | Titre | Durée | Cumul | Preuve à l'écran |
| ---: | --- | ---: | ---: | --- |
| 1 | Diagnostic de roulements par vibrations | 0 min 30 s | 0 min 30 s | Question et identité |
| 2 | Données CWRU et séparation des essais | 0 min 55 s | 1 min 25 s | Tableau des quatre charges |
| 3 | Tâche 1 · indicateurs temporels | 1 min 00 s | 2 min 25 s | Distributions RMS, kurtosis, facteur de crête |
| 4 | Tâche 2 · fréquences de défaut et enveloppe | 1 min 00 s | 3 min 25 s | BPFO/BPFI et spectres annotés |
| 5 | Tâche 3 · fenêtre et résolution FFT | 0 min 50 s | 4 min 15 s | 1 s, 12 000 points, 1 Hz ; enveloppe 1,111 Hz |
| 6 | Tâche 4 · quatre expériences appariées | 1 min 00 s | 5 min 15 s | Tableau E1–E4 |
| 7 | Résultats du développement | 1 min 20 s | 6 min 35 s | Graphique natif des scores de développement |
| 8 | Tâche 5 · transfert à 3 HP | 1 min 25 s | 8 min 00 s | Graphique natif des scores finaux |
| 9 | Erreurs finales de la forêt enrichie | 1 min 10 s | 9 min 10 s | Matrice native de 92 fenêtres et 10/10 essais |
| 10 | Conclusion et limites | 0 min 50 s | 10 min 00 s | Scores, gain, intervalle et limites |

## 1. Diagnostic de roulements par vibrations

**Écran :** « CWRU · quatre états · transfert de charge », Mouhamedou Yahya Cheikh Med Vall, 25239.

**Notes :** Présenter le diagnostic sain, bague interne, bague externe et bille. Poser la question de l'apport des caractéristiques d'enveloppe et du transfert à une charge absente de l'apprentissage.

## 2. Données CWRU et séparation des essais

**Écran :** 40 essais, dix par charge. Charges 0–2 HP : 30 essais de développement. Charge 3 HP : dix essais de test final. Sains à 48 kHz, défauts DE à 12 kHz, analyse à 12 kHz.

**Notes :** Chaque pli valide une charge entière. Un FIR causal de coupure 4,8 kHz traite les deux fréquences natives. Deux vitesses d'essais sains viennent de valeurs officielles approximatives faute de mesures dans les MAT. Sources : `data/classcoverage.csv`, `data/splits/recordings.csv`, `docs/data_audit.md`.

## 3. Tâche 1 · indicateurs temporels

**Écran :** `results/figures/temporal_features.png`, avec RMS, kurtosis de Pearson et facteur de crête.

**Notes :** Retirer la moyenne locale. RMS mesure l'amplitude efficace, la kurtosis la part des valeurs extrêmes, et le facteur de crête compare le pic à RMS. Ce sont les trois caractéristiques de E1. Une différence visuelle de distribution ne prouve pas seule la qualité de classification.

## 4. Tâche 2 · fréquences de défaut et enveloppe

**Écran :** `BPFO = 3,5848 × rpm/60`, `BPFI = 5,4152 × rpm/60`, et `presentation/envelope_examples.png`, recalculée avec les mêmes fonctions sur deux essais du développement, sans modèle ni donnée finale.

**Notes :** Les facteurs viennent de la [fiche CWRU du roulement](https://engineering.case.edu/bearingdatacenter/bearing-information). Le passe-bande causal 2–5 kHz précède l'enveloppe calculée sur une fenêtre fermée. Les trois premières harmoniques sont mesurées pour toutes les classes. La vraie étiquette ne choisit pas les bandes. La bande fixe n'est pas présentée comme la résonance optimale de chaque essai.

## 5. Tâche 3 · fenêtre et résolution FFT

**Écran :** 1 s, 12 000 échantillons, `Δf = 1 Hz`. L'enveloppe conserve 0,9 s après coupe des bords : `Δf ≈ 1,111 Hz`.

**Notes :** La fenêtre de Hann réduit la fuite, mais élargit les pics. Le pas des raies de 1 Hz n'assure pas la séparation de deux pics distants de 1 Hz. Une prédiction attend la fin de la fenêtre. Source : `docs/features.md`.

## 6. Tâche 4 · quatre expériences appariées

**Écran :** E1 arbre et trois caractéristiques, E2 arbre et 13, E3 forêt et trois, E4 forêt et 13. Le tableau est modifiable.

**Notes :** Les quatre expériences utilisent les mêmes 268 fenêtres hors pli et les mêmes charges de validation. Les métadonnées de classe, charge et groupe restent hors de la matrice `X`. Comparer E2 à E1 et E4 à E3 pour l'effet des caractéristiques ; E3 à E1 pour l'effet du classifieur.

## 7. Résultats du développement

**Écran :** Graphique natif modifiable, exactitude équilibrée pondérée par enregistrement : E1 92,90 %, E2 87,35 %, E3 95,06 %, E4 99,69 %. Différences : E2−E1 −5,56 points ; E4−E3 +4,63 points.

**Notes :** E4 a été sélectionné sur le développement avant la lecture de 3 HP. Les nouvelles caractéristiques aident la forêt et pénalisent l'arbre dans ce protocole. L'ablation mesure dix nouvelles colonnes ensemble ; elle n'isole pas l'enveloppe seule. Source : `results/summary.csv`.

## 8. Tâche 5 · transfert à 3 HP

**Écran :** Graphique natif modifiable : E1 90,74 %, E2 98,15 %, E3 89,81 %, E4 98,15 %. Même métrique que sur le développement.

**Notes :** Après gel, une campagne a évalué les quatre modèles sur 92 fenêtres de dix essais à 3 HP. E2 et E4 ont le même score final. E4 reste le modèle sélectionné avant le test. Sources : `results/summary.csv`, `results/final_metrics.json`.

## 9. Erreurs finales de la forêt enrichie

**Écran :** Matrice native modifiable, lignes vraies et colonnes prédites dans l'ordre sain, bague interne, bague externe, bille :

| Vrai / prédit | Sain | Interne | Externe | Bille |
| --- | ---: | ---: | ---: | ---: |
| Sain | 9 | 0 | 0 | 0 |
| Interne | 0 | 28 | 0 | 0 |
| Externe | 0 | 0 | 26 | 2 |
| Bille | 0 | 0 | 0 | 27 |

**Notes :** Deux fenêtres de bague externe sont prises pour la bille. Après agrégation des probabilités, E4 classe correctement les dix essais. Le rappel pondéré de bague externe est 92,59 %. Les fenêtres voisines ne comptent pas comme essais indépendants. Source : `results/final_metrics.json`.

## 10. Conclusion et limites

**Écran :** E4 99,69 % en développement, 98,15 % à 3 HP. E4−E1 : +7,41 points à 3 HP, bootstrap par essai à 95 % `[0 ; 17,59 points]`.

**Notes :** La borne basse de l'intervalle touche zéro. Le test final n'a qu'un essai sain et l'identité du roulement physique entre charges n'est pas connue. Les résultats concernent le banc CWRU étudié et ne démontrent pas un déploiement industriel. Une répétition humaine chronométrée reste à faire. Source : `results/final_bootstrap.json`.
