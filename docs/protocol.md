# Mouhamedou Yahya Cheikh Med Vall
# 25239
# Maryeim Mohamed T'Feil
# 22087

# Protocole expérimental fixé avant entraînement

Date : 20 novembre 2026. Sources de vérité : `configs/experiment.json`, `data/manifest.csv`, `data/splits/recordings.csv` et `ARCHITECTURE.md`.

## Population et frontières

Quarante enregistrements DE : quatre sains et 36 défauts de bague interne, bague externe à 6 h et bille, de diamètres 0,007/0,014/0,021 pouce. Les charges 0/1/2 HP donnent 30 essais de développement. Dix essais à 3 HP restent réservés au test final.

Les plis de développement utilisent `GroupKFold(3)` avec la charge comme supergroupe : validation sur 2, puis 1, puis 0 HP. Ce choix fondé sur les métadonnées préserve chaque enregistrement et garantit toutes les classes dans chaque pli. Chaque validation possède un seul essai sain. La dépendance éventuelle d'un même roulement physique entre essais n'est pas identifiable et limite la généralisation.

## Préparation et variables

Signaux sains à 48 kHz selon Radtke et Bock (2022), défauts à 12 kHz selon la table CWRU. Les sains sont filtrés causalement avant décimation à 12 kHz. Ce traitement différent peut laisser un effet d'acquisition associé à la classe ; il sera discuté et ne constitue pas une preuve de généralisation industrielle.

Fenêtres de 1 s sans recouvrement. Pas de recherche de durée sur scores. Passe-bande causal de 2 à 5 kHz, ordre 4, fixé comme bande haute large sous Nyquist ; pas de recherche optimisant cette bande. Exclusion des transitoires et des bords de Hilbert selon la configuration. Les preuves de réponse fréquentielle et les figures du développement doivent vérifier son usage avant les modèles. Ce choix ne prétend pas identifier automatiquement une résonance optimale.

Trois variables de référence et dix variables spectrales/enveloppe, conformément à `FULL_FEATURES`. Toutes les classes reçoivent les mêmes variables. `Normal_1` et `Normal_2` utilisent la vitesse approximative de la table officielle, explicitement distinguée d'une mesure MAT ; l'erreur des bandes de ces essais reste une limite.

## Comparaison fixée

E1 : arbre et trois indicateurs. E2 : arbre et treize indicateurs. E3 : forêt et trois indicateurs. E4 : forêt et treize indicateurs. Grille : profondeurs 3, 6 et sans limite ; feuilles minimales 1 et 5 ; forêt de 200 arbres ; graine 313. La meilleure moyenne des exactitudes équilibrées par pli, avec poids égal de chaque enregistrement, choisit les réglages. Une égalité préfère la profondeur plus petite puis la feuille plus grande. Une égalité entre expériences préfère E1, E2, E3, puis E4.

Les scores de développement servent à la sélection ; ils ne sont pas une estimation indépendante après sélection. La charge finale fournit l'évaluation réservée. Les quatre expériences annoncées sont évaluées ensemble une fois leurs paramètres gelés.

## Mesures et interprétation

Exactitude, exactitude équilibrée, macro-F1, rappel par classe et matrices de confusion brutes et normalisées. Présenter les scores par fenêtre, avec pondération égale des essais, et le diagnostic par essai par moyenne des probabilités. Le bootstrap apparié rééchantillonne les essais dans chaque classe, 1 000 fois avec graine 313. Un seul sain à 3 HP ne permet pas d'estimer sa variabilité entre essais. Aucun seuil minimal de performance n'est exigé et un gain nul ou négatif est conservé.

Le code exige un gel des sources scientifiques, données, partitions, configuration, choix du développement et environnement. Un marqueur est écrit avant l'extraction finale. Toute nouvelle variante après consultation du test reste exploratoire.
