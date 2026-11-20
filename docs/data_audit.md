# Mouhamedou Yahya Cheikh Med Vall
# 25239
# Maryeim Mohamed T'Feil
# 22087

# Audit des données CWRU et partitions

Audit réalisé le 20 novembre 2026, avant tout entraînement. Les fichiers MAT originaux sont conservés dans `data/raw/`. Le manifeste donne l'URL de chaque fichier, ses empreintes SHA-256, sa clé DE et ses métadonnées. `data/audit.json` garde les contrôles d'intégrité par fichier. `data/classcoverage.csv` compte les enregistrements par classe et charge.

## Sources et choix du sous-ensemble

Les [tables officielles des défauts DE à 12 kHz](https://engineering.case.edu/bearingdatacenter/12k-drive-end-bearing-fault-data) donnent trois types de défaut, trois diamètres (0,007, 0,014 et 0,021 pouce), quatre charges et la position de défaut externe à 6 h. La [table officielle des essais sains](https://engineering.case.edu/bearingdatacenter/normal-baseline-data) donne un essai pour chaque charge. Les 40 liens MAT de ces deux tables ont été téléchargés. La page [Data Files](https://engineering.case.edu/bearingdatacenter/download-data-file) explique les clés `DE`, `FE`, `BA` et `RPM`. La [procédure du banc](https://engineering.case.edu/bearingdatacenter/apparatus-and-procedures) décrit les capteurs et les défauts artificiels.

La table saine ne précise pas sa fréquence. L'article de [Radtke et Bock (2022), section 4.1.1](https://papers.phmsociety.org/index.php/phme/article/download/3329/1947), identifie les données de référence saines à 48 kHz et les défauts DE à 12 kHz. Le manifeste conserve donc 48 000 Hz pour les quatre essais sains et 12 000 Hz pour les 36 défauts. Le fichier MAT ne contient pas de champ explicite de fréquence : cette information vient des sources, et non d'un calcul sur la longueur du signal. Une conversion des signaux sains vers 12 kHz devra utiliser un filtre anti-repliement en M3.

Les pages consultées ne donnent pas clairement l'unité numérique des valeurs d'accélération. Le manifeste la marque comme non précisée. La charge et la vitesse approximative viennent des tables officielles. La vitesse `rpm` dans le manifeste provient seulement de la clé MAT propre au fichier. Cette clé est absente de `Normal_1` et `Normal_2` : leur vitesse mesurée reste vide ; les valeurs approximatives de la table, 1 772 et 1 750 tr/min, sont conservées dans `rpm_table_approx`. `rpm_used` prend la valeur MAT lorsqu'elle existe, sinon la valeur de la table. `rpm_source` et `rpm_is_approximate` rendent ce remplacement visible. Ces deux vitesses de travail ne sont pas des mesures. Les futures bandes BPFO/BPFI devront tenir compte de cette incertitude ; une tolérance étroite de 3 Hz ne peut pas être garantie pour ces deux essais sans borne d'erreur de la vitesse publiée.

## Résultats de l'audit

| Contrôle | Résultat |
| --- | ---: |
| Fichiers MAT téléchargés | 40 |
| Empreintes SHA-256 de fichiers distinctes | 40 |
| Empreintes SHA-256 des signaux DE propres distinctes | 40 |
| Signaux contenant une valeur non finie | 0 |
| Plus longue suite de valeurs identiques | 3 échantillons |
| Essais avec une vitesse MAT manquante | 2 (`Normal_1`, `Normal_2`) |
| Enregistrements exclus | 0 |

Chaque fichier contient la clé DE qui correspond à son numéro de fichier. `99.mat` contient aussi des clés portant un autre numéro ; seule `X099_DE_time` est le signal propre de `Normal_2`. Les clés additionnelles ne deviennent pas de nouveaux enregistrements. Les bornes numériques et le nombre de répétitions des extrema figurent dans `data/audit.json`. Ces contrôles ne prouvent pas l'absence de saturation : la plage du convertisseur n'est pas documentée. Aucun pic ni échantillon répété n'a été supprimé.

Le nombre d'échantillons DE va de 121 265 à 122 917 pour les défauts, et de 243 938 à 485 643 pour les signaux sains. La durée est calculée par `n_samples / fs_native_hz`. Il n'y a pas d'horodatage de chaque échantillon ni de chronologie des essais entre fichiers. Deux empreintes différentes ne démontrent pas l'indépendance des roulements physiques. Les essais de charges différentes peuvent partager un roulement défectueux ; la source ne fournit pas l'identifiant physique permettant de le vérifier.

## Couverture et partitions

| Charge (HP) | Sain | Bague interne | Bille | Bague externe | Total |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1 | 3 | 3 | 3 | 10 |
| 1 | 1 | 3 | 3 | 3 | 10 |
| 2 | 1 | 3 | 3 | 3 | 10 |
| 3 | 1 | 3 | 3 | 3 | 10 |

La charge 3 HP est réservée comme test final. Les charges 0, 1 et 2 HP forment le développement. `GroupKFold(n_splits=3)` reçoit la charge comme supergroupe : chaque pli valide sur une charge entière et apprend sur les deux autres. Ce choix déterministe repose uniquement sur les métadonnées et garantit les quatre classes dans chaque partie. Chaque validation a 10 enregistrements : un sain et trois par type de défaut. `data/splits/recordings.csv` enregistre le pli de validation de chaque essai ; le test final porte `fold = -1`. `data/splits/split_plan.json` décrit la règle. Aucun fichier source, alias ou groupe `group_id` ne traverse l'apprentissage et la validation d'un pli.

La classe saine ne fournit qu'un essai par charge. L'évaluation par pli mesure donc très mal la variabilité des essais sains. Les plis sont aussi des transferts entre charges ; leurs scores futurs ne seront pas une estimation d'un échantillonnage aléatoire de nouveaux essais à charge identique. La charge 3 HP n'a servi qu'aux contrôles d'intégrité et de métadonnées de cet audit. Aucune caractéristique ni performance de cette charge n'a servi à choisir la partition.

## Reproduction

Depuis la racine du projet, exécuter `PYTHONPATH=src .venv/bin/python -c "from pathlib import Path; from bearing_diagnosis.data import acquire_and_audit; from bearing_diagnosis.splits import build_splits; m=acquire_and_audit(Path('.')); build_splits(m, Path('.'))"`. Si un fichier déjà présent ne correspond plus à l'empreinte du manifeste, l'acquisition s'arrête au lieu de le remplacer silencieusement. Les téléchargements ne sont pas versionnés ; leurs URL et empreintes le sont dans `data/manifest.csv`.
