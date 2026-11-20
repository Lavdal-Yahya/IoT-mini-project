# Mouhamedou Yahya Cheikh Med Vall
# 25239
# Maryeim Mohamed T'Feil
# 22087

# Présentation web CWRU

**[Ouvrir la version web privée](https://cwru-group7-vibration-lab.fuzzychest.chatgpt.site)**

Dix diapositives interactives, avec Apache ECharts **6.1.0**. La bibliothèque et la police Manrope sont incorporées avec leurs licences. Aucune ressource externe n’est nécessaire pour afficher les graphiques.

## Ouvrir en local

Depuis la racine du dépôt :

```sh
python -m http.server 8765 --directory presentation/web/dist
```

Ouvrir `http://localhost:8765`. Aucun paquet npm ni serveur applicatif n’est nécessaire. Les fragments `#1` à `#10` désignent les diapositives. Naviguer avec Précédente/Suivante ou les flèches. `P` ouvre le plan, `N` les notes et `F` le plein écran. Les commandes de lecture actualisent le contexte de chaque graphique et les tableaux exacts. Les animations natives ECharts se rejouent à chaque apparition de diapositive : tracé des lignes, croissance des barres et apparition échelonnée des points et cellules. Le redimensionnement ne redémarre pas la séquence. Elles respectent aussi les changements de la préférence de réduction du mouvement.

Le support est un oral explicatif de dix minutes estimées. Ses interactions lisent les résultats sauvegardés, sans nouvelle sélection du modèle. Le score de développement est signalé comme optimiste, les populations sont distinguées et le sain final unique reste une limite visible.

## Sources et reconstruction

`build_data.py` reconstruit `dist/data.js` depuis les métriques gelées, les médianes des caractéristiques du développement et deux fenêtres de développement à préparation fixe. Il vérifie l’empreinte de la table de caractéristiques. Il ne lance aucun entraînement ni recherche de paramètres.

```sh
PYTHONPATH=src .venv/bin/python presentation/web/build_data.py
```

Les données CWRU et une extraction reproduite sont nécessaires pour reconstruire les séries. Les fichiers déjà livrés sous `dist/` suffisent pour consulter la présentation. Les graphes sont définis dans `dist/charts.js`, la navigation dans `dist/app.js` et le style dans `dist/style.css`. Le premier signal est un extrait réel de 50 ms de IR007_0. Les deux spectres reprennent la première fenêtre des deux essais de développement déjà illustrés dans le PowerPoint.

## Vérifier

Les dépendances de contrôle restent séparées du verrou scientifique :

```sh
npm install --prefix tmp/web-qa jsdom@26.1.0 --ignore-scripts --no-audit --no-fund
node presentation/web/check_web.cjs
node presentation/web/check_animations.cjs
```

Le contrôle DOM vérifie les auteurs, les dix diapositives, les raccourcis, les commandes de lecture, leurs dénominateurs et les tableaux. ECharts rend réellement 38 états SVG : 19 combinaisons pertinentes en largeurs 900 et 360 pixels. Les métriques sont comparées aux preuves gelées.

Cette vérification ne remplace pas une inspection complète en navigateur. Le navigateur local est désactivé dans les réglages Work. Des rendus SVG représentatifs ont été inspectés et l’aperçu HTTP a répondu 200 ; cette limite figure dans `verification.json`.

## Publication

`.openai/hosting.json` conserve l’identité du Site privé. Le workflow Sites publie depuis une copie temporaire du dossier, sans dépôt Git imbriqué dans le projet. `deployment.json` conserve l’URL et le résultat confirmé du service. Le code scientifique et les supports précédents restent distincts de cette présentation web.

Les contrôles d’animation exécutent la vraie bibliothèque ECharts dans un DOM simulé : démarrage natif, fin sans boucle, rejeu à la revisite, conservation des valeurs et arrêt immédiat en réduction du mouvement. Ce contrôle ne remplace pas une revue visuelle dans un navigateur. Référence API : [transitions ECharts](https://echarts.apache.org/handbook/en/how-to/animation/transition/).
