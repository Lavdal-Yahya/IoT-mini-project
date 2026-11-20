# Mouhamedou Yahya Cheikh Med Vall
# 25239
# Maryeim Mohamed T'Feil
# 22087

# Vérification de la reproductibilité

Le 20 novembre 2026, un second environnement Python 3.12.14 a été créé dans `.venv-repro/`, sans accès aux paquets du premier environnement. Les dépendances ont été installées depuis `requirements.lock.txt`, puis le paquet local avec `pip install -e . --no-deps`.

La commande `.venv-repro/bin/python -m bearing_diagnosis.cli reproduce` a refait les vérifications des données, les partitions et les caractéristiques. Elle a réentraîné E1–E4 avec les paramètres gelés, sans nouvelle recherche. Les 368 prédictions de fenêtre du test final sont identiques à la référence, avec comparaison des probabilités à une tolérance de 1e-12. Cela ne constitue pas une seconde expérience indépendante.

Preuve : `results/reproduction_verification.json`. Les 32 tests automatisés couvrent les calculs de signal, les métriques, les partitions, le gel et les chemins de reproduction. Les pages du rapport ont été rendues et inspectées. Ces contrôles ne remplacent ni de nouveaux essais physiques ni une répétition de la soutenance.

Le gel scientifique est `results/freeze.json`. Les variables de présentation restent séparées du calcul scientifique. Les signaux ne sont pas distribués dans Git ; `data/manifest.csv` contient les sources et empreintes nécessaires pour les récupérer.

Un clone Git distinct, initialement sans `outputs/`, a ensuite été contrôlé avec le même environnement neuf. Seul le cache MAT a été copié et ses empreintes revérifiées. Le clone a restauré le registre livré, reconstruit les caractéristiques et reproduit les prédictions, puis régénéré les figures. Preuve : `results/clean_clone_verification.json`. Le réseau des tables officielles a été utilisé ; les fichiers bruts n’ont pas été retéléchargés pendant ce second contrôle.
