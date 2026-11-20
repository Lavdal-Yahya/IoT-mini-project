# Mouhamedou Yahya Cheikh Med Vall
# 25239

# Caractéristiques vibratoires : méthode et limites

## Entrée et préparation

`extract_recording(x, row, config)` reçoit un canal brut d'un seul essai et sa ligne de manifeste. Il crée des fenêtres complètes de 1 s, sans recouvrement, à 12 000 Hz. Il ignore le fragment terminal et le compte dans `DataFrame.attrs['preparation']`. Il ne mélange jamais deux essais.

`prepare_signal_with_metadata` applique un FIR passe-bas causal à **tous** les signaux. La coupure fixe est 4 800 Hz. La durée du filtre est ajustée à la fréquence native : 161 coefficients à 48 kHz et 41 à 12 kHz. Le filtre Hamming utilise `lfilter`. À 48 kHz, un échantillon sur quatre est ensuite conservé ; à 12 kHz, aucun échantillon n'est décimé. Cette règle rapproche la réponse numérique des deux voies et protège le passage 48→12 kHz contre le repliement. Les autres rapports entiers restent à vérifier avant inclusion. Les 0,1 premières secondes de la grille d'analyse sont exclues après ce filtrage. Le passe-bande enlève encore 0,1 s de démarrage aux deux voies. Les signaux bruts ne sont pas modifiés.

Le FIR causal a un délai de groupe nominal de 80 échantillons natifs à 48 kHz ou de 20 à 12 kHz, soit 1,67 ms dans les deux cas. Ce délai n'est pas compensé avec des échantillons futurs. `DataFrame.attrs['preparation']` contient le facteur, la coupure, ce délai, les effectifs et les échantillons retirés. `start_sample` et `stop_sample` (exclu) sont sur la grille d'analyse, **avant** retrait de la période initiale. `native_start_sample` et `native_stop_sample` (exclu) donnent les bornes natives des échantillons utilisés. `available_at_s` est le plus tardif de la fin nominale de fenêtre et de l’arrivée du dernier échantillon natif nécessaire. Il faut attendre la fin de la fenêtre. Ces temps sont relatifs au début du fichier, sans horodatage réel.

## Tâche 1 — indicateurs temporels

Pour chaque fenêtre, la moyenne locale est soustraite. Ensuite :

- `rms = sqrt(mean(x²))` ;
- `kurtosis` est la kurtosis de Pearson, avec correction d'échantillon `bias=False` de SciPy. Une loi gaussienne a pour référence 3 ;
- `crest_factor = max(abs(x)) / rms`.

Une fenêtre constante, non finie ou trop courte provoque une erreur explicite. Aucun ajustement d'amplitude par fenêtre n'est fait. La baseline utilise exactement ces trois colonnes, dans `BASE_FEATURES`.

## Tâches 2 et 3 — spectre, roulement et enveloppe

`spectrum` retire la moyenne, applique une fenêtre de Hann périodique, puis une FFT réelle. L'amplitude est divisée par la somme des coefficients de Hann. Les raies intérieures sont doublées ; 0 Hz et Nyquist ne le sont pas. Une sinusoïde centrée sur une raie retrouve ainsi son amplitude crête. Pour 12 000 points à 12 kHz, l'espacement des raies vaut `Δf = fs/N = 1 Hz`. La fenêtre de Hann élargit le lobe principal : deux pics espacés de 1 Hz ne sont pas forcément séparables. Après exclusion des bords, le spectre d’enveloppe utilise 0,9 s et son espacement vaut environ 1,111 Hz.

Les facteurs publiés pour le roulement côté entraînement CWRU donnent `BPFO = 3,5848 × rpm/60` et `BPFI = 5,4152 × rpm/60`, en Hz ([fiche CWRU](https://engineering.case.edu/bearingdatacenter/bearing-information)). La vitesse provient de la métadonnée de chaque essai. Ces facteurs ne doivent pas être appliqués à un autre roulement sans vérification. La classe vraie n'entre dans aucun calcul de caractéristique.

L'enveloppe suit cette chaîne : passe-bande Butterworth d'ordre 4 à 2 000–5 000 Hz par `sosfilt` causal sur l'essai → transformée de Hilbert **sur chaque fenêtre fermée** → module → exclusion de 0,05 s à chaque bord → retrait de la moyenne → Hann et FFT. Le filtre passe-bande est réinitialisé au début de chaque essai. La bande est une proposition initiale sous Nyquist (6 kHz), avec une largeur permettant de garder une porteuse haute fréquence et ses bandes latérales à quelques centaines de hertz. Aucune résonance propre à un essai CWRU n'a encore été confirmée. Ce choix doit être contrôlé sur le développement, jamais sur la charge finale.

Les colonnes enrichies ajoutent les centroïdes et entropies normalisées des spectres bruts et d'enveloppe, puis la part d'énergie d'enveloppe située à ±3 Hz des harmoniques 1, 2 et 3 de BPFO et BPFI. Le dénominateur est l'énergie spectrale hors composante continue. Toutes les bandes candidates sont calculées pour toutes les classes. `FULL_FEATURES` fixe l'ordre des 13 colonnes. Les métadonnées de classe, charge, groupe et partition restent hors de cette liste et hors de la matrice `X`.

## Vérification actuelle

Les tests synthétiques contrôlent la convention de kurtosis, les cas dégénérés, l'amplitude et l'espacement FFT, les facteurs DE, l'atténuation d'une composante à 8 kHz avant décimation, et la récupération d'une modulation de 100 Hz dans une porteuse à 3 kHz. Ils vérifient aussi les bornes, l'heure de disponibilité et l'indépendance des caractéristiques vis-à-vis de l'étiquette. Ces essais ne prouvent pas le choix de bande ni la qualité du diagnostic sur CWRU. Les figures et comparaisons expérimentales restent à produire sur les données auditées.

## Diagnostic numérique des filtres avant les modèles

`check_filter_diagnostics(config)` fournit un dictionnaire sérialisable. Il ne lit aucun fichier CWRU. Avec les paramètres proposés, la réponse du passe-bande vaut environ −0,001 dB à 3 kHz, −1,80 dB à 2,1 kHz et −0,43 dB à 4,8 kHz. Elle vaut −31,3 dB à 1 kHz et −29,2 dB à 5,5 kHz. Le délai de groupe maximal calculé entre 2,1 et 4,8 kHz est de 0,624 ms. Après les 0,1 s retirées, la fraction d'énergie de la réponse impulsionnelle restante est inférieure à 10⁻¹⁵⁰ dans ce calcul. Ces mesures concernent le filtre fixe ; elles ne démontrent pas que 2–5 kHz porte une résonance utile sur les données.

À 48→12 kHz, la réponse du FIR est environ −0,69 dB à 4,5 kHz, −6,01 dB à 4,8 kHz et −14,93 dB à 5 kHz. Son gain maximal au-dessus de 6 kHz est inférieur à −59 dB. La version 12 kHz donne environ −0,71, −6,00 et −14,97 dB aux mêmes fréquences. L'écart des gains 12 kHz moins 48 kHz vaut moins de 0,04 dB à ces trois points. Le haut de la bande d'enveloppe est donc réduit dans les deux voies. Ce rapprochement numérique ne rend pas identiques les acquisitions physiques à 12 et 48 kHz ; leur répartition par classe et charge reste à signaler dans l'audit.

Sur une porteuse synthétique stationnaire à 3 033,3 Hz modulée à 107,544 Hz, l'erreur maximale de l'enveloppe analytique atteint 0,238 au bord de la fenêtre. Après retrait de 0,05 s par bord, elle reste sous 0,002 pour cet exemple. Ce contrôle motive la coupe des bords ; il ne borne pas l'erreur pour tous les signaux.
