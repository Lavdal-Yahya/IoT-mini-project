# Mouhamedou Yahya Cheikh Med Vall
# 25239

# Roadmap du mini-projet AML313 du groupe 7

Création : **19 novembre 2026**. Dernière mise à jour : **20 novembre 2026**.

## 1. Rôle et autorité

Ce fichier est la source de vérité pour le but, le périmètre, les étapes, les jalons et l'avancement. [ARCHITECTURE.md](ARCHITECTURE.md) définit leur réalisation technique. L'[énoncé](Mini-projet-AML313.pdf), pages 3, 10 et 12, reste la référence pédagogique. Les instructions explicites de l'utilisateur priment ; toute adaptation est documentée.

Un jalon est terminé quand ses preuves existent et ont été vérifiées. Un script écrit mais non exécuté ne prouve pas un résultat. Les cases de la section 6 constituent l'unique suivi d'avancement ; le README sert de point d'entrée.

## 2. But et hypothèse

**But :** reconnaître quatre états d'un roulement — sain, défaut de bague interne, défaut de bague externe, défaut de bille — à partir des vibrations CWRU, avec des indicateurs physiques interprétables et une validation sans fuite entre enregistrements.

**Question expérimentale :** les caractéristiques spectrales et d'enveloppe apportent-elles une information utile au-delà de RMS, kurtosis et facteur de crête ? Le diagnostic reste-t-il valable sur une charge absente de l'apprentissage ?

**Hypothèse initiale, écrite avant tout modèle :** les indicateurs d'enveloppe proches de BPFO et BPFI devraient réduire certaines confusions entre défauts. Le transfert de charge pourrait dégrader la performance. Ces propositions sont à tester ; aucun gain n'est présumé.

**Baseline imposée :** RMS + kurtosis + facteur de crête, puis arbre de décision. Une forêt aléatoire est proposée comme modèle plus riche. L'ablation séparera l'effet des caractéristiques de celui du classifieur.

## 3. Périmètre et réussite

Le projet comprend le diagnostic des fichiers, la préparation journalisée, les indicateurs temporels et spectraux, BPFO/BPFI, l'enveloppe, la classification, l'ablation et le transfert vers une autre charge. Le sous-ensemble exact, les canaux et la fréquence commune seront confirmés après audit.

La durée de vie restante, une application web, un déploiement industriel et les réseaux profonds sont hors du périmètre initial. Leur ajout demanderait de réviser les objectifs et la charge de travail.

Le projet est réussi lorsque :

- Les cinq tâches du sujet ont chacune une méthode, une réalisation et une preuve vérifiable.
- Baseline, modèle plus riche et ablation utilisent les mêmes observations et partitions.
- Aucun enregistrement source, alias ou doublon de signal ne traverse les partitions.
- Exactitude et matrices de confusion sont complétées par une analyse par classe, par enregistrement et une incertitude adaptée aux groupes.
- Une charge entière est réservée avant les essais pour le test final de transfert ; elle ne sert pas au réglage.
- Les résultats et figures sont reproductibles avec les données identifiées et un environnement figé.
- L'article et la soutenance expliquent les choix physiques, les erreurs et les limites.

Il n'y a pas de seuil arbitraire de performance. Un modèle plus riche qui ne bat pas la baseline reste un résultat recevable si le protocole et la conclusion sont rigoureux.

## 4. Étapes et jalons

| Jalon | Travail | Preuves et condition de fin |
| --- | --- | --- |
| M0 — Cadrage | Lire les consignes et références ; écrire le but, la baseline et l'hypothèse. | Roadmap, architecture et règles de suivi cohérentes avec le sujet. |
| M1 — Audit | Inventorier les sources ; télécharger le sous-ensemble candidat ; vérifier canaux, fréquences, unités, vitesses, charges, tailles, positions des défauts et qualité. | Manifeste avec provenance et empreintes ; tableau classe × charge × enregistrement ; journal d'audit et limites connues. |
| M2 — Protocole | Fixer le sous-ensemble, les groupes, la charge finale, les plis, les fenêtres, les métriques et le budget d'essais. | Configuration et partitions enregistrées ; couverture des classes et absence de fuite vérifiées ; protocole fixé avant tout entraînement. |
| M3 — Analyse physique | Préparer les signaux ; calculer les trois indicateurs, BPFO/BPFI, FFT et enveloppe ; justifier durée, fenêtrage et bande. | Caractéristiques traçables ; figures sain/défectueux issues du développement ; calculs physiques vérifiés. |
| M4 — Modèles et ablation | Comparer arbre et forêt, avec et sans caractéristiques spectrales, sur les plis de développement. | Résultats appariés des quatre expériences ; matrices de confusion hors pli ; choix justifié ; test final non consulté. |
| M5 — Transfert final | Figer les décisions ; réentraîner sur le développement ; exécuter une campagne finale sur la charge réservée. | Protocole gelé ; prédictions, métriques et incertitude ; analyse du transfert sans réglage ultérieur. |
| M6 — Livraison | Vérifier la reproduction ; rédiger l'article ; préparer la soutenance et vérifier le barème. | Une commande pour reproduire ; environnement figé ; README utilisable ; article 4–6 pages ; présentation 10 min et préparation aux 5 min de questions. |

Ordre : **M0 → M1 → M2 → M3 → M4 → M5 → M6**. Un chargement ou contrôle du signal est autorisé pendant l'audit ; l'entraînement attend M2. Si un diagnostic invalide un choix, réviser le protocole et le documenter avant les essais concernés.

## 5. Livrables et couverture de l'énoncé

| Exigence | Jalon | Preuve principale |
| --- | --- | --- |
| Tâche 1 — RMS, kurtosis, facteur de crête | M3 | Calculs et comparaison sain/défectueux. |
| Tâche 2 — BPFO/BPFI et enveloppe | M3 | Métadonnées du roulement, calculs et spectres annotés. |
| Tâche 3 — Résolution FFT et fenêtre | M2, M3 | Durée, nombre de points, `Δf` et justification du fenêtrage. |
| Tâche 4 — Classification et modèle plus riche | M4 | Baseline, forêt et ablation. |
| Tâche 5 — Autre charge | M2, M5 | Charge réservée et bilan du transfert. |
| Validation sans fuite — 4 points au barème | M2, M4, M5 | Groupes, prétraitements par pli, gel et test unique. |
| Diagnostic, préparation, incertitude et reproductibilité | M1 à M6 | Audit, journaux, métriques et relance complète. |
| Dépôt GitHub et article scientifique | M6 | Dépôt reproductible ; article 4–6 pages avec ablation et limites. |
| Soutenance | M6 | Support de 10 min et préparation aux 5 min de questions. |

## 6. Avancement

- [x] M0 — Cadrage documentaire terminé.
- [ ] M1 — Audit des données. **Prochain jalon.**
- [ ] M2 — Protocole fixé.
- [ ] M3 — Analyse physique et caractéristiques vérifiées.
- [ ] M4 — Modèles et ablation évalués sur le développement.
- [ ] M5 — Test final de transfert réalisé.
- [ ] M6 — Livraison et reproduction vérifiées.

**État observé :** l'énoncé et les documents de cadrage sont présents. Le dépôt Git est initialisé sur `main`, avec `origin` configuré vers [Lavdal-Yahya/IoT-mini-project](https://github.com/Lavdal-Yahya/IoT-mini-project). Les pages officielles CWRU ont été consultées pour préparer l'architecture. Aucun signal n'a été téléchargé, aucun modèle entraîné et aucun résultat expérimental produit.

**Prochaine action :** construire le manifeste des enregistrements candidats à partir des tables officielles, puis vérifier les fichiers en M1.

## 7. Budget indicatif

Le cadre pédagogique propose 1 h 30 de diagnostic, 6 h de construction et 3 h de validation/rédaction, soit 10 h 30. Ce sont des repères de charge, pas des dates de livraison.

| Phase | Jalons principaux | Repère |
| --- | --- | --- |
| Diagnostic | M1 et définition de M2 | 1 h 30 |
| Construction | Finalisation de M2, M3, M4 | 6 h |
| Validation et rédaction | M5, M6 | 3 h |

Consigner les difficultés et délais de données. Si le budget est insuffisant, réduire les essais ou variantes optionnelles en conservant les exigences du sujet.

## 8. Risques et réponses

| Risque ou inconnue | Réponse prévue |
| --- | --- |
| Fréquences ou canaux hétérogènes | Vérification par fichier ; harmonisation avec anti-repliement ou révision du sous-ensemble. |
| Peu d'enregistrements sains indépendants | Contrôle des classes par pli ; adaptation sur métadonnées avant les scores ; limites d'incertitude explicites. |
| Même signal sous plusieurs noms | Empreintes de fichier et de signal ; regroupement des alias avant partitionnement. |
| Classification artificiellement facile | Contrôle des confusions avec fréquence, durée, charge, taille et position du défaut ; transfert. |
| Bande ou fenêtre choisie sur le test | Sélection physique ou développement uniquement ; paramètres gelés avant M5. |
| Banc CWRU différent d'une machine en service | Décrire les défauts artificiels et limiter la conclusion au diagnostic étudié. |

## 9. Maintenir le cap

Après chaque étape significative, mettre à jour les preuves, les cases, la prochaine action et les inconnues. Modifier aussi l'architecture lorsqu'un choix technique, une interface ou le protocole change. Les paramètres exécutés doivent correspondre à la configuration enregistrée.

Après consultation du test final, une nouvelle idée reste exploratoire et ne peut pas être annoncée comme confirmée par ce même test. Une relance technique identique est permise pour la reproductibilité ; elle ne sert pas à sélectionner une nouvelle méthode.

| Date | Changement | Conséquence |
| --- | --- | --- |
| 2026-11-19 | Création de la roadmap et de l'architecture. | M0 terminé ; M1 à commencer ; propositions techniques identifiées. |
| 2026-11-20 | Initialisation du dépôt Git sur `main`, configuration d'`origin` et ajout de `.gitignore`. | Dépôt limité au mini-projet ; cours et TPs conservés dans le workspace parent ; M1 reste le prochain jalon. |
