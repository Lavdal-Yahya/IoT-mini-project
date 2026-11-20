# Mouhamedou Yahya Cheikh Med Vall
# 25239

# Plan de soutenance — mini-projet AML313, groupe 7

**Durée visée : 10 min (estimation par sections, sans répétition chronométrée).** Ce document prépare l'oral ; il n'est pas un jeu de diapositives. Les chiffres proviennent de `results/summary.csv`, `results/final_metrics.json` et `results/final_bootstrap.json`. La répétition humaine reste à faire.

| Section | Durée | Cumul | Message à retenir |
| --- | ---: | ---: | --- |
| 1. Question et hypothèse | 0 min 45 s | 0 min 45 s | Quatre états du roulement ; tester l'apport de l'enveloppe et le transfert de charge. |
| 2. Données et séparation | 1 min 15 s | 2 min 00 s | 40 essais CWRU ; 30 pour le développement, 10 à 3 HP réservés. |
| 3. Tâche 1 — indicateurs temporels | 1 min 10 s | 3 min 10 s | RMS, kurtosis de Pearson et facteur de crête forment la baseline. |
| 4. Tâche 2 — fréquences de défaut et enveloppe | 1 min 20 s | 4 min 30 s | BPFO/BPFI guident des bandes calculées pour toutes les classes. |
| 5. Tâche 3 — fenêtre et FFT | 1 min 00 s | 5 min 30 s | Une seconde à 12 kHz donne un pas FFT brut de 1 Hz. |
| 6. Tâche 4 — modèles et ablation | 1 min 50 s | 7 min 20 s | Comparer arbre et forêt avec 3 puis 13 caractéristiques, sur les mêmes plis. |
| 7. Tâche 5 — transfert de charge | 1 min 50 s | 9 min 10 s | Examiner 3 HP une seule fois après gel du protocole. |
| 8. Conclusion et limites | 0 min 50 s | 10 min 00 s | Dire ce que les résultats soutiennent, puis leurs limites. |

## 1. Question et hypothèse — 0 min 45 s

**À dire.** « Nous cherchons à distinguer un roulement sain de trois défauts : bague interne, bague externe et bille. La question est de savoir si les caractéristiques spectrales et d'enveloppe ajoutent de l'information aux trois indicateurs temporels. Nous testons aussi si le diagnostic tient sur une charge absente de l'apprentissage. »

**Note orale.** Annoncer une hypothèse, pas une conclusion : BPFO/BPFI pourraient aider à réduire certaines confusions ; le changement de charge pourrait dégrader les scores. Aucun gain n'est présumé.

## 2. Données et séparation — 1 min 15 s

**À dire.** « L'audit contient 40 fichiers CWRU côté entraînement : quatre essais sains et 36 essais avec défaut. Chaque charge, de 0 à 3 HP, donne dix essais : un sain et neuf défectueux. Les charges 0, 1 et 2 HP forment le développement. La charge 3 HP, soit dix essais, est réservée au test final. »

**Note orale.** Les défauts DE sont à 12 kHz et les essais sains à 48 kHz selon les sources de l'audit. Un FIR causal de coupure 4,8 kHz est appliqué aux **deux** fréquences natives, avec 41 ou 161 coefficients, avant l'analyse à 12 kHz. Signaler que les vitesses de deux essais sains manquent dans les MAT : les valeurs utilisées sont des approximations de la table officielle, non des mesures. Les fichiers d'une même source et leurs fenêtres restent dans le même groupe. Les trois plis du développement valident chacun sur **une charge entière** (validation « leave one load out »).

**Source à montrer.** `data/classcoverage.csv`, `data/splits/recordings.csv` et `docs/data_audit.md`.

## 3. Tâche 1 — indicateurs temporels — 1 min 10 s

**À dire.** « Après retrait de la moyenne locale, nous calculons l'énergie RMS, la kurtosis de Pearson corrigée du biais et le facteur de crête. Ces trois valeurs constituent le modèle de référence imposé. Elles sont calculées sur les mêmes fenêtres que les caractéristiques enrichies. »

**Note orale.** `RMS = √moyenne(x²)` et `facteur de crête = max|x| / RMS`. La kurtosis mesure le poids des valeurs extrêmes ; la référence gaussienne est 3. Une fenêtre constante ou non finie est refusée. Montrer la distribution sain/défaut issue **uniquement** du développement. Ne pas lire une différence de distribution comme preuve de classification.

**Figure disponible.** Distribution : `results/figures/temporal_features.png`.

## 4. Tâche 2 — fréquences de défaut et enveloppe — 1 min 20 s

**À dire.** « Pour le roulement DE étudié, `BPFO = 3,5848 × rpm/60` et `BPFI = 5,4152 × rpm/60`. Nous filtrons causalement entre 2 et 5 kHz, puis calculons l'enveloppe sur une fenêtre terminée. Les énergies proches de trois harmoniques BPFO et BPFI sont mesurées pour **toutes** les classes. L'étiquette ne choisit jamais la bande. »

**Note orale.** Préciser qu'un bord de 0,05 s est retiré de chaque côté de l'enveloppe, après 0,1 s de démarrage pour le FIR et 0,1 s pour le passe-bande. La bande 2–5 kHz est fixée physiquement sous Nyquist et vérifiée sur le développement, sans optimisation sur 3 HP. L’ablation a ensuite testé l’utilité des caractéristiques enrichies, sans isoler la seule enveloppe. Deux vitesses approximatives déplacent les bandes théoriques ; la tolérance de ±3 Hz n'en efface pas l'incertitude.

**Figure disponible.** Spectre d'enveloppe annoté : `results/figures/spectra_envelope.png`.

## 5. Tâche 3 — fenêtre et FFT — 1 min 00 s

**À dire.** « Une fenêtre complète dure une seconde et contient 12 000 échantillons à 12 kHz. Son espacement FFT est donc `Δf = fs/N = 1 Hz`. La moyenne est retirée avant une fenêtre de Hann. Ce pas de 1 Hz ne signifie pas que deux pics distants de 1 Hz sont séparables. »

**Note orale.** La correction du gain cohérent de Hann permet de lire l'amplitude crête d'une sinusoïde placée sur une raie. L'enveloppe conserve 0,9 s après coupe des bords : son pas FFT est environ 1,111 Hz. La décision ne peut être disponible qu'à la fin de la fenêtre. Les filtres causaux ont un délai de groupe documenté ; aucune date réelle n'est inventée.

## 6. Tâche 4 — modèles et ablation — 1 min 50 s

**À dire.** « Nous comparons quatre expériences appariées : E1, arbre sur trois indicateurs ; E2, arbre sur 13 ; E3, forêt sur trois ; E4, forêt sur 13. Ainsi, E2 contre E1 et E4 contre E3 mesurent l'apport des caractéristiques. E3 contre E1 et E4 contre E2 mesurent l'effet du classifieur. Les observations et les trois charges de validation restent identiques. »

**Note orale.** Les 13 colonnes réunissent trois indicateurs temporels, quatre caractéristiques générales des spectres et six rapports d'énergie d'enveloppe BPFO/BPFI. Les métadonnées de classe, charge, identité et partition sont exclues de `X`. Présenter l'exactitude équilibrée, la matrice de confusion et le résultat par enregistrement. Avec un seul essai sain par charge, l'incertitude entre essais sains est mal estimée.

**Résultat vérifié.** Sur les 30 enregistrements de développement (268 fenêtres hors pli), l'exactitude équilibrée avec poids égal par enregistrement vaut **92,90 % pour E1**, **87,35 % pour E2**, **95,06 % pour E3** et **99,69 % pour E4**. Le modèle E4 a été retenu avant le test final. Les 13 caractéristiques diminuent le score de l'arbre de **5,56 points** (E2−E1), mais augmentent celui de la forêt de **4,63 points** (E4−E3). Il faut donc parler d'une interaction avec le classifieur, pas d'un bénéfice uniforme des nouvelles caractéristiques. Montrer `results/figures/ablation.png` et `results/figures/development_scores.png`. Source : `results/summary.csv`.

## 7. Tâche 5 — transfert de charge — 1 min 50 s

**À dire.** « Après avoir fixé caractéristiques, filtres, modèles et métriques sur les charges 0–2 HP, nous réentraînons sur tout ce développement. Nous évaluons alors les quatre expériences en une campagne sur la charge 3 HP réservée. »

**Note orale.** Afficher les prédictions par enregistrement, pas seulement la proportion de fenêtres correctes. Les fenêtres voisines ne sont pas des essais indépendants : l'incertitude est évaluée au niveau des enregistrements. Un résultat à 3 HP reflète à la fois charge et différence entre essais. Des défauts à diverses charges peuvent même provenir du même roulement physique ; l'identifiant physique n'est pas fourni. Ne pas appeler cela une preuve de généralisation à une autre machine.

**Résultat vérifié.** La campagne finale unique couvre 92 fenêtres de dix enregistrements. L'exactitude équilibrée pondérée par enregistrement vaut **90,74 % pour E1**, **98,15 % pour E2**, **89,81 % pour E3** et **98,15 % pour E4**. E4, choisi sur le développement, classe correctement les dix enregistrements après agrégation. Il se trompe toutefois sur deux fenêtres de bague externe, attribuées à la bille : le rappel pondéré de cette classe est **92,59 %**, contre 100 % pour les trois autres. Montrer `results/figures/final_window_confusion.png` et distinguer clairement l'unité « fenêtre » de l'unité « essai ». Pour E4−E1, le gain est **7,41 points**, avec intervalle bootstrap à 95 % **[0 ; 17,59] points** par rééchantillonnage des enregistrements. La classe saine n'a qu'un essai final : cet intervalle n'estime pas sa variation entre essais. Sources : `results/summary.csv`, `results/final_metrics.json`, `results/final_bootstrap.json`.

## 8. Conclusion et limites — 0 min 50 s

**À dire.** « Sur le développement, la forêt enrichie E4 atteint 99,69 % d'exactitude équilibrée, contre 92,90 % pour l'arbre de référence E1. Sur la charge 3 HP réservée, E4 atteint 98,15 % contre 90,74 % pour E1. Les caractéristiques enrichies aident la forêt dans cette comparaison ; elles ont réduit le score de l'arbre sur le développement. »

**Note orale.** Terminer par trois limites précises : peu d'essais sains indépendants, vitesse seulement approximative pour deux sains, et dépendance physique possible entre charges. Les filtres numériques sont rapprochés entre 12 et 48 kHz, mais les acquisitions d'origine ne deviennent pas identiques. L’intervalle bootstrap E4−E1 atteint 0 à sa borne basse ; dix essais finaux ne permettent pas une conclusion générale forte. Une répétition chronométrée reste à faire.
