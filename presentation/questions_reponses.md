# Mouhamedou Yahya Cheikh Med Vall
# 25239
# Maryeim Mohamed T'Feil
# 22087

# Questions et réponses — soutenance AML313

Ces réponses préparent les cinq minutes de questions. Les scores cités viennent de `results/summary.csv` et les limites d’incertitude de `results/final_bootstrap.json`. Le minutage oral n’a pas été vérifié par répétition humaine.

## 1. Pourquoi ne pas répartir les fenêtres au hasard ?

Les fenêtres d'un même enregistrement partagent le signal, le capteur et les conditions de l'essai. Les mélanger entre apprentissage et validation donnerait au modèle une partie de la source qu'il doit reconnaître. Nous gardons donc chaque essai, ses fenêtres et ses copies dans un même groupe. La charge 3 HP est réservée entière.

## 2. Les groupes garantissent-ils l'indépendance physique ?

Ils empêchent le partage direct d'un fichier, d'un signal ou de ses fenêtres. Ils ne prouvent pas que deux charges ont utilisé des roulements physiques différents. La source ne fournit pas l'identifiant du roulement. Nous présentons les plis par charge comme un transfert entre conditions, avec cette limite explicite.

## 3. Pourquoi trois plis « leave one load out » ?

Les charges 0, 1 et 2 HP sont les trois conditions de développement. À chaque pli, deux charges servent à apprendre et la troisième à valider. Chacune contient les quatre classes. Cette règle vérifie un changement de charge sans toucher à 3 HP. Elle est fixée à partir des métadonnées, avant les scores.

## 4. Quelle différence entre BPFO et BPFI ?

BPFO désigne la fréquence théorique de passage sur un défaut de bague externe ; BPFI celle de bague interne. Pour le roulement côté entraînement CWRU, elles valent respectivement 3,5848 et 5,4152 fois la fréquence de rotation `rpm/60`. Elles placent des bandes d'analyse ; elles ne sont pas des étiquettes ni une preuve qu'un défaut est présent.

## 5. La vitesse approximative des deux essais sains pose-t-elle problème ?

Oui. Leurs fichiers MAT n'ont pas de vitesse mesurée. Les valeurs de la table officielle sont utilisées et marquées comme approximatives. Une erreur de vitesse déplace BPFO/BPFI et leurs harmoniques. La tolérance de ±3 Hz n'a pas de garantie physique pour ces deux essais. Les résultats sur la classe saine doivent être lus avec cette limite.

## 6. Pourquoi un passe-bande 2–5 kHz et une enveloppe ?

Un défaut peut moduler une vibration de plus haute fréquence. Le passe-bande garde une zone large sous le Nyquist de 6 kHz, puis l'enveloppe cherche des répétitions proches de BPFO/BPFI. La bande a été fixée avant les scores du test final. Nous n'affirmons pas qu'elle est la résonance optimale de chaque essai. Son utilité est jugée par l'ablation sur le développement.

## 7. Le filtrage à 48 kHz rend-il les signaux comparables aux 12 kHz ?

Il réduit une différence de traitement numérique : le même passe-bas causal de coupure 4,8 kHz est appliqué aux deux sources. Il a 161 coefficients à 48 kHz et 41 à 12 kHz, avec la même durée et un délai nominal de 1,67 ms. Les réponses calculées diffèrent de moins de 0,04 dB aux points contrôlés entre 4,5 et 5 kHz. Cela ne supprime pas une éventuelle différence d'acquisition d'origine. Le sain vient de fichiers 48 kHz, les défauts de 12 kHz ; c'est une limite du sous-ensemble.

## 8. Pourquoi une fenêtre de 1 s ? Le pas FFT de 1 Hz est-il la résolution réelle ?

Une seconde donne 12 000 points à 12 kHz et un pas de raie de 1 Hz. Hann réduit la fuite spectrale mais élargit les pics. Deux composantes à 1 Hz d'écart ne sont donc pas forcément séparables. L'enveloppe perd 0,05 s à chaque bord et son pas est environ 1,111 Hz. La décision attend la fin de la fenêtre.

## 9. Que mesure la kurtosis et pourquoi Pearson ?

Elle quantifie le poids des valeurs extrêmes après retrait de la moyenne locale. Nous utilisons la convention de Pearson avec correction du biais ; une loi gaussienne a pour référence 3. Nous fixons cette convention pour toutes les fenêtres. Une kurtosis élevée peut suggérer des chocs, sans prouver leur origine.

## 10. Comment éviter que 13 caractéristiques gagnent seulement parce que le modèle est plus complexe ?

Nous comparons E2 à E1 avec le même arbre, puis E4 à E3 avec la même forêt, sur les mêmes fenêtres et partitions. Sur le développement, les 13 caractéristiques font **baisser** l’exactitude équilibrée de l’arbre de 5,56 points, mais font **monter** celle de la forêt de 4,63 points. L’effet dépend donc du classifieur. L’ablation porte sur l’ensemble des dix nouvelles colonnes ; elle ne mesure pas l’apport de l’enveloppe seule. E4 a été choisi sur le développement avant la campagne finale.

## 11. Pourquoi l'exactitude seule ne suffit-elle pas ?

Il y a peu d'enregistrements indépendants, et les essais peuvent avoir des nombres de fenêtres différents. Un score brut par fenêtre peut donner trop de poids aux essais longs. Nous présentons l'exactitude équilibrée, les rappels par classe, la matrice de confusion et un bilan par enregistrement. Sur le test final, E4 classe correctement les dix essais après agrégation, tout en confondant deux des 28 fenêtres de bague externe avec la bille. Une incertitude calculée sur les fenêtres comme si elles étaient indépendantes serait trop optimiste.

## 12. Le test sur 3 HP prouve-t-il une généralisation industrielle ?

Non. Il évalue une charge non vue sur ce banc CWRU et ce sous-ensemble. Il change aussi les essais, et peut conserver une dépendance physique entre charges. Les défauts sont artificiels. Une autre machine, un autre capteur ou des défauts naturels demanderaient une nouvelle évaluation.

## 13. Et si l'enveloppe ne dépasse pas la baseline ?

L’ablation des caractéristiques spectrales et d’enveloppe montre un effet contrasté : l’enrichissement pénalise l’arbre E2, mais aide la forêt E4. Sur 3 HP, E2 et E4 atteignent tous deux 98,15 % d’exactitude équilibrée pondérée. Nous rapportons les quatre expériences sans modifier les paramètres après lecture du test. Une autre bande ou un autre modèle serait exploratoire et demanderait de nouvelles données.

## 14. Le gain final E4 contre E1 est-il certain ?

Le gain mesuré est de 7,41 points d’exactitude équilibrée pondérée. Le bootstrap par enregistrement donne un intervalle à 95 % de 0 à 17,59 points. La borne basse atteint zéro. Le test ne contient qu’un essai sain et trois essais par type de défaut ; l’intervalle ne mesure donc pas bien la variabilité possible entre essais, surtout pour la classe saine.

## 15. Pourquoi retenir E4 si E2 a le même score final ?

E4 a été choisi avant de voir 3 HP, sur les plis de développement : 99,69 % d’exactitude équilibrée, contre 87,35 % pour E2. Sur le test final, les deux atteignent 98,15 %. Cette égalité observée ne justifie pas de refaire le choix après consultation du test.
