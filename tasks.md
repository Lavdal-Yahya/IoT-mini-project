# Mouhamedou Yahya Cheikh Med Vall
# 25239

# Tâches du mini-projet AML313 du groupe 7

Dernière mise à jour : **20 novembre 2026**.

## Mode d'emploi

Cette checklist traduit les jalons de [ROADMAP.md](ROADMAP.md) en actions ordonnées. La roadmap reste la référence pour les objectifs, le périmètre et l'état des jalons. [ARCHITECTURE.md](ARCHITECTURE.md) reste la référence technique. Ce fichier porte uniquement l'exécution détaillée des tâches.

Suivre les identifiants dans l'ordre. Une case cochée signifie que la preuve indiquée existe et a été vérifiée. Ajouter sa commande, son résultat ou son chemin à la ligne concernée lors de la clôture. Les chemins annoncés ci-dessous sont des sorties à produire ; leur présence dans cette liste ne signifie pas qu'ils existent déjà.

Après chaque étape, mettre à jour cette checklist et le jalon correspondant dans la roadmap. Ne terminer un jalon que lorsque toutes ses tâches obligatoires sont closes. Si une tâche devient non applicable, conserver son identifiant et expliquer pourquoi. Toute adaptation scientifique actualise aussi l'architecture et la configuration.

**Prochaine tâche : T31 — vérifier les métriques puis comparer les modèles sur le développement.** Les paramètres encore provisoires de l'architecture seront confirmés par l'audit, avant les essais concernés.

## M0 — Cadrer le projet

- [x] **T01 — Lire l'énoncé et identifier les exigences du groupe 7.** Preuve : PDF présent ; tâches et livrables repris dans la roadmap.
- [x] **T02 — Écrire le but, la question, l'hypothèse et la baseline avant tout entraînement.** Preuve : sections 2 et 3 de la roadmap.
- [x] **T03 — Définir l'architecture et les règles de suivi.** Preuve : `ARCHITECTURE.md`, `AGENTS.md`, README et présente checklist.
- [x] **T04 — Initialiser le dépôt et publier le cadrage initial.** Preuve : commit initial `2def44a` sur `main`, poussé vers le dépôt GitHub configuré ; `.gitignore` présent.

## M1 — Auditer les données

Prérequis : M0 terminé. Aucun entraînement dans cette phase.

- [x] **T05 — Inventorier les enregistrements candidats dans les tables officielles CWRU.** Relever liens, classes, charges, tailles et positions des défauts. Preuve : première version de `data/manifest.csv`, avec informations inconnues signalées. **Vérifié :** data/manifest.csv : 40 sources officielles.
- [x] **T06 — Préparer l'environnement et les outils d'acquisition.** Créer le paquet minimal, l'environnement isolé et les fonctions de téléchargement/lecture nécessaires à l'audit. Preuve : imports réussis, dépendances déclarées et versions exactes enregistrées. **Vérifié :** Python 3.12.14, pyproject.toml, requirements.lock.txt ; pip check réussi.
- [x] **T07 — Télécharger les fichiers candidats sans modifier les originaux.** Respecter les conditions d'utilisation et conserver la provenance. Preuve : fichiers sous `data/raw/`, URL et empreintes SHA-256 dans le manifeste. **Vérifié :** 40 fichiers téléchargés ; empreintes vérifiées lors du second audit.
- [x] **T08 — Inspecter les fichiers MAT et vérifier les métadonnées.** Identifier canaux, dimensions, unités, fréquence native et vitesse. Preuve : manifeste complété avec source de chaque métadonnée ; fichiers incertains mis en attente. **Vérifié :** data/manifest.csv ; deux RPM approximatifs tracés.
- [x] **T09 — Contrôler la qualité des signaux.** Quantifier valeurs non finies, saturation, séquences constantes, durées et autres anomalies. Preuve : journal d'audit, sans suppression automatique des pics ni imputation silencieuse. **Vérifié :** data/audit.json : aucune valeur non finie ; saturation non certifiable.
- [x] **T10 — Identifier les doublons, alias et liens entre enregistrements.** Comparer empreintes des fichiers et signaux, puis attribuer `recording_id` et `group_id`. Preuve : groupes documentés et copies regroupées ; indépendance physique non présumée. **Vérifié :** 40 empreintes de fichiers et de signaux distinctes ; propre clé X099 sélectionnée.
- [x] **T11 — Compter les enregistrements par classe et charge.** Vérifier notamment le nombre d'essais sains et la faisabilité du transfert. Preuve : tableau classe × charge × groupe, avec exclusions justifiées. **Vérifié :** data/classcoverage.csv : quatre classes à chaque charge.
- [x] **T12 — Rédiger le bilan d'audit et confirmer le sous-ensemble admissible.** Conserver le diagnostic final dans `outputs/<run_id>/` et ses conclusions durables dans l'architecture. Preuve : manifeste vérifié, limites explicites et M1 mis à jour dans la roadmap. **Vérifié :** docs/data_audit.md et data/audit.json.

## M2 — Fixer le protocole avant l'entraînement

Prérequis : M1 terminé. Les contrôles de partitionnement précèdent les modèles.

- [x] **T13 — Écrire la configuration de l'expérience.** Confirmer classes, canal, tailles de défaut, fréquence d'analyse, graines et critères d'inclusion. Preuve : `configs/experiment.json` et décisions D04–D07 actualisées selon les résultats de l'audit. **Vérifié :** configs/experiment.json et docs/protocol.md.
- [x] **T14 — Réserver la charge du test final de transfert.** Confirmer ou réviser la proposition 3 HP à partir des métadonnées uniquement. Preuve : liste des enregistrements réservés dans `data/splits/`, sans consultation de scores. **Vérifié :** data/splits/recordings.csv : dix enregistrements à 3 HP réservés.
- [x] **T15 — Construire les plis de développement avec GroupKFold.** Confirmer leur nombre et vérifier la présence des classes dans chaque apprentissage et évaluation. Preuve : affectations enregistrées et tableau de couverture des classes par pli. **Vérifié :** data/splits/split_plan.json : trois validations par charge entière.
- [x] **T16 — Vérifier les frontières entre partitions.** Contrôler groupes, canaux, copies et dérivés ; documenter l'absence de chronologie réelle si elle n'est pas fournie. Preuve : contrôles exécutés, sans enregistrement source partagé entre partitions. **Vérifié :** tests/test_splits.py et audit des empreintes.
- [x] **T17 — Fixer les fenêtres et les règles de préparation.** Définir durée, pas, fragments exclus, retrait de moyenne, rééchantillonnage éventuel et disponibilité de la prédiction. Preuve : configuration initiale et justification de `Δf = fs / N` ; comparaison éventuelle de durées limitée au développement. **Vérifié :** Fenêtres fixes 1 s ; configuration et docs/protocol.md.
- [x] **T18 — Fixer les métriques, E1–E4 et le budget de sélection.** Définir pondération par enregistrement, agrégation des probabilités, départage des modèles, grille bornée et méthode d'incertitude. Preuve : règles précises dans la configuration, avant les scores. **Vérifié :** Grille E1–E4 et métriques fixées dans docs/protocol.md.
- [x] **T19 — Vérifier la cohérence du protocole avec la baseline et l'hypothèse.** Identifier les paramètres de signal restant à justifier sur le développement en M3 et interdire tout réglage sur la charge finale. Preuve : configuration et partitions versionnées ; M2 clôturé avant le premier entraînement. **Vérifié :** Audit et partitions vérifiés ; hypothèse antérieure à tout entraînement.

## M3 — Préparer les signaux et extraire les indicateurs

Prérequis : M2 terminé. Les exemples et réglages de signal viennent du développement.

- [x] **T20 — Implémenter la préparation traçable des signaux.** Appliquer les décisions sur fréquence, composante continue, bords et transitoires ; préserver les originaux. Preuve : `signals.py` et journal des transformations avec paramètres et effectifs. **Vérifié :** Code signals.py/features.py ; tests numériques réussis ; résultats de développement dans results/figures/ et journal outputs/main/preparation_development.json.
- [x] **T21 — Construire les fenêtres avec leur provenance.** Conserver identifiants source, bornes, fréquence et instant de disponibilité ; compter les fragments exclus. Preuve : index de fenêtres conforme au contrat de l'architecture. **Vérifié :** Code signals.py/features.py ; tests numériques réussis ; résultats de développement dans results/figures/ et journal outputs/main/preparation_development.json.
- [x] **T22 — Vérifier les trois calculs temporels sur des signaux connus.** Tester RMS, kurtosis de Pearson, facteur de crête et cas dégénérés. Preuve : contrôles numériques exécutés, conventions et tolérances explicites. **Vérifié :** Code signals.py/features.py ; tests numériques réussis ; résultats de développement dans results/figures/ et journal outputs/main/preparation_development.json.
- [x] **T23 — Extraire les trois caractéristiques de la baseline.** Utiliser les mêmes fenêtres pour toutes les expériences. Preuve : table de caractéristiques temporelles sans métadonnées interdites dans `X`. **Vérifié :** Code signals.py/features.py ; tests numériques réussis ; résultats de développement dans results/figures/ et journal outputs/main/preparation_development.json.
- [x] **T24 — Calculer les fréquences de défaut pour chaque essai.** Vérifier le roulement, la vitesse, BPFO et BPFI avec leurs sources. Preuve : table de fréquences en Hz, sans géométrie ni vitesse inventée. **Vérifié :** Code signals.py/features.py ; tests numériques réussis ; résultats de développement dans results/figures/ et journal outputs/main/preparation_development.json.
- [x] **T25 — Implémenter et vérifier la FFT.** Contrôler Hann, normalisation, unités et résolution sur une sinusoïde connue. Preuve : pic correctement localisé et comparaison documentée de la résolution attendue et observée. **Vérifié :** Code signals.py/features.py ; tests numériques réussis ; résultats de développement dans results/figures/ et journal outputs/main/preparation_development.json.
- [x] **T26 — Choisir et vérifier le passe-bande d'enveloppe.** Justifier la bande à partir de la physique et du développement ; mesurer délais et transitoires. Preuve : paramètres enregistrés, réponse fréquentielle et portions exclues documentées. **Vérifié :** results/filter_diagnostics.json : gains, délais, transitoires et réponses 12/48 kHz comparées avant entraînement.
- [x] **T27 — Implémenter et vérifier l'enveloppe.** Tester une porteuse modulée connue, puis inspecter les effets de bord sur le développement. Preuve : modulation retrouvée ; méthode disponible seulement à la fin de la fenêtre annoncée. **Vérifié :** Code signals.py/features.py ; tests numériques réussis ; résultats de développement dans results/figures/ et journal outputs/main/preparation_development.json.
- [x] **T28 — Définir et extraire les caractéristiques spectrales.** Fixer bandes, harmoniques et tolérances ; calculer les mêmes candidats pour toutes les classes. Preuve : dictionnaire des caractéristiques et table enrichie traçable. **Vérifié :** Code signals.py/features.py ; tests numériques réussis ; résultats de développement dans results/figures/ et journal outputs/main/preparation_development.json.
- [x] **T29 — Produire les comparaisons physiques sain/défectueux.** Montrer distributions des trois indicateurs, FFT et enveloppes avec BPFO/BPFI annotées. Preuve : figures légendées issues du développement, avec unités et interprétation. **Vérifié :** Code signals.py/features.py ; tests numériques réussis ; résultats de développement dans results/figures/ et journal outputs/main/preparation_development.json.
- [x] **T30 — Contrôler et enregistrer l'extraction complète.** Vérifier clés uniques, dimensions, nombres finis, exclusions et alignement avec les partitions. Preuve : tables validées, tests exécutés et choix de signal actualisés dans l'architecture ; M3 clôturé. **Vérifié :** 268 fenêtres de développement, 13 caractéristiques finies ; 32 tests réussis ; figures inspectées.

## M4 — Comparer les modèles et mener l'ablation

Prérequis : M3 terminé. Aucun résultat de la charge finale n'est consulté.

- [ ] **T31 — Implémenter l'évaluation commune.** Calculer exactitude, matrices de confusion, rappels, exactitude équilibrée et macro-F1 selon les pondérations annoncées. Preuve : contrôles sur un petit exemple dont les résultats sont calculables à la main.
- [ ] **T32 — Implémenter l'entraînement par pli.** Ajuster modèles et prétraitements appris seulement sur l'apprentissage ; conserver les prédictions hors pli. Preuve : provenance des apprentissages et contrôles de séparation.
- [ ] **T33 — Évaluer E1, la baseline imposée.** Arbre de décision sur RMS, kurtosis et facteur de crête. Preuve : paramètres, scores par pli et prédictions hors pli enregistrés.
- [ ] **T34 — Évaluer E2.** Arbre avec caractéristiques temporelles et spectrales/enveloppe. Preuve : mêmes fenêtres et partitions que E1.
- [ ] **T35 — Évaluer E3.** Forêt aléatoire avec les trois indicateurs temporels. Preuve : mêmes entrées que E1 et réglages conformes à la grille annoncée.
- [ ] **T36 — Évaluer E4.** Forêt avec caractéristiques temporelles et spectrales/enveloppe. Preuve : mêmes observations et protocole que E1–E3.
- [ ] **T37 — Analyser les ablations, erreurs et incertitudes.** Comparer E2 à E1 et E4 à E3 pour les caractéristiques, puis E3 à E1 et E4 à E2 pour le classifieur. Preuve : gains appariés, confusion par classe et limites de l'incertitude par groupe.
- [ ] **T38 — Arrêter les choix du développement.** Retenir les réglages selon le critère fixé, sans exiger que le modèle enrichi gagne. Preuve : décision écrite, résultats et configuration sauvegardés ; M4 clôturé.

## M5 — Évaluer le transfert une seule fois

Prérequis : M4 terminé. **Ne pas commencer l'évaluation finale avant T39 et T40.**

- [ ] **T39 — Produire le fichier de gel.** Enregistrer empreintes des données, groupes, code, configuration, caractéristiques, bandes, modèles et métriques. Preuve : protocole final identifiable, sans paramètre scientifique ouvert.
- [ ] **T40 — Vérifier la commande de test et son suivi de consultation.** Exiger le gel, empêcher la sélection sur scores finaux et écrire le marqueur de consultation au début de l'accès évaluatif. Preuve : contrôle du mécanisme avec des données de contrôle distinctes du test réel.
- [ ] **T41 — Réentraîner les expériences annoncées sur tout le développement.** Garder les paramètres gelés et tracer les sources utilisées. Preuve : modèles E1–E4 et métadonnées d'entraînement sauvegardés.
- [ ] **T42 — Exécuter la campagne finale sur la charge réservée.** Évaluer E1–E4 dans la même campagne et conserver toutes les prédictions. Preuve : résultats finaux identifiés, sans sélection ni réglage après lecture.
- [ ] **T43 — Interpréter le transfert et ses limites.** Présenter exactitude, confusions, résultats par enregistrement et incertitude ; distinguer effet de charge et différences d'essais. Preuve : bilan honnête, y compris les dégradations et les classes peu représentées.
- [ ] **T44 — Clôturer le test final.** Enregistrer le statut consulté et les références des résultats ; classer toute nouvelle idée comme exploratoire. Preuve : M5 clôturé et aucune variante ultérieure présentée comme confirmée par ce test.

## M6 — Reproduire et livrer

Prérequis : M5 terminé pour les résultats finaux. Un premier brouillon des limites peut être écrit dès M1.

- [ ] **T45 — Finaliser la commande de reproduction.** Relier acquisition vérifiée, préparation, extraction, développement figé et génération des sorties. Preuve : interface documentée ; les relances identiques du test restent distinguées d'une nouvelle sélection scientifique.
- [ ] **T46 — Vérifier la reproduction dans un environnement propre.** Installer les versions figées et relancer le protocole. Preuve : commande réelle, versions, résultats comparés et éventuelles différences numériques expliquées.
- [ ] **T47 — Générer les tables et figures finales depuis les sorties sauvegardées.** Éviter la recopie manuelle des chiffres. Preuve : chaque élément de l'article peut être relié à une exécution et à ses prédictions.
- [ ] **T48 — Rédiger l'article de 4 à 6 pages.** Couvrir données, préparation, baseline, modèle, validation, résultats avec incertitude, ablation et limites. Preuve : document complet, chiffres cohérents et références vérifiables.
- [ ] **T49 — Préparer la soutenance de 10 minutes.** Présenter question, méthode, physique, protocole, résultats et limites ; préparer les 5 minutes de questions. Preuve : support final et répétition chronométrée.
- [ ] **T50 — Finaliser le README et les instructions de lancement.** Documenter installation, acquisition, commandes disponibles, organisation et accès aux résultats. Preuve : parcours utilisable depuis un clone neuf, sans dépendance aux cours locaux pour exécuter le code.
- [ ] **T51 — Vérifier la livraison avec les cinq tâches et le barème.** Contrôler reproductibilité, article, figures, sources, soutenance et absence de fichiers locaux indésirables. Preuve : couverture de l'énoncé vérifiée et fichiers de livraison sélectionnés.
- [ ] **T52 — Versionner et publier la livraison finale.** Préserver les données brutes hors Git, sélectionner les résultats à partager et vérifier la synchronisation du dépôt. Preuve : commit de livraison identifié ; roadmap, architecture et checklist cohérentes ; M6 clôturé.
