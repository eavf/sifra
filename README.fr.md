# Déchiffrement d'un chiffre par substitution — `decrypt_revised2.py`

🇸🇰 [Slovensky](README.sk.md) | 🇬🇧 [English](README.md) | 🇫🇷 Français

---

## Contexte — de quoi s'agit-il ?

Un exercice classique de lycée : étant donné un texte chiffré et un tableau de fréquences des lettres, est-il possible de le déchiffrer en utilisant uniquement les fréquences des caractères individuels — sans bigrammes ni trigrammes ?

La réponse courte : **pas automatiquement**. Un tableau de fréquences ne donne qu'une estimation initiale grossière. De nombreuses lettres ont des fréquences similaires (par exemple `s`, `n`, `r`, `t`, `i` en français se situent toutes entre 6 et 8 %), ce qui rend le classement peu fiable. Ce que les élèves faisaient réellement, c'était combiner l'indice fréquentiel avec des essais manuels et une intuition linguistique — en devinant des mots à partir d'un contexte partiel. Les bigrammes et trigrammes automatisent précisément cette intuition.

Ce programme reproduit ce processus de manière algorithmique, en combinant **analyse fréquentielle** et **recuit simulé**.

---

## Constat clé — la qualité des données est déterminante

Le facteur le plus important pour la qualité du déchiffrement est **la taille et la précision des tables de fréquences des n-grammes**. Une première version n'utilisant que ~40 bigrammes et ~50 trigrammes produisait un texte illisible ; l'extension des tables à **~250 bigrammes et ~100 trigrammes** a immédiatement donné un déchiffrement quasi-parfait — une amélioration bien plus importante que tout réglage algorithmique (plus de redémarrages, plus d'itérations, poids des trigrammes, etc.).

La fonction de scoring ne peut distinguer un bon français d'un mauvais que si elle dispose de suffisamment de données de référence. Avec trop peu de n-grammes, presque chaque paire de lettres reçoit la même pénalité, et l'algorithme ne parvient pas à s'orienter vers la solution correcte.

---

## Le chiffre par substitution — principe

Un chiffre par substitution utilise une **clé** secrète — un tableau de 26 paires associant chaque lettre du texte clair à une lettre du texte chiffré :

```
texte clair:   a b c d e f g ...
texte chiffré: r x k o f p q ...
```

Chaque `a` devient `r`, chaque `b` devient `x`, etc. Le résultat ressemble à du bruit aléatoire, mais il **conserve les propriétés statistiques de la langue d'origine** — certaines lettres apparaissent toujours plus souvent que d'autres. C'est précisément ce qui permet de casser le chiffre sans connaître la clé.

---

## Fichiers du projet

| Fichier | Description |
|---|---|
| `decrypt_revised2.py` | Script principal |
| `crypt.txt` | Texte chiffré en entrée |
| `french_character_frequencies.csv` | Fréquences des lettres en français (26 lettres) |
| `french_bigram_frequencies.csv` | Fréquences des bigrammes en français (~250 paires) |
| `french_trigram_frequencies.csv` | Fréquences des trigrammes en français (~100 triplets) |
| `stat.csv` | Source alternative de fréquences (format : `caractère;fréquence`) |
| `preklady/` | Répertoire de sortie pour les résultats (créé automatiquement) |
| `test/` | Suite de tests |

Les tables de fréquences proviennent de [sttmedia.com](https://www.sttmedia.com/characterfrequency-french) et ont été étendues pour une meilleure couverture.

---

## Comment exécuter

```bash
python3 decrypt_revised2.py
```

Tous les fichiers d'entrée doivent se trouver dans le même répertoire que le script.
Le résultat est affiché dans la console et sauvegardé dans `preklady/preklad_Rev2_YYYYMMDD_HHMMSS.txt`.

---

## Algorithme — étape par étape

### Étape 0 — Détection de chiffre de César (pré-vérification)

`try_caesar()`

Avant de lancer le recuit simulé (coûteux en calcul), l'algorithme teste les 25 décalages possibles de César. Un chiffre de César applique le même décalage fixe à chaque lettre (par exemple toutes les lettres décalées de 4). Si le meilleur décalage produit un score suffisamment élevé, le résultat est utilisé directement et le recuit simulé est entièrement ignoré.

Pour les chiffres par substitution générale (où chaque lettre a un mapping indépendant), les scores de César seront très bas et l'algorithme poursuivra avec l'optimisation complète.

---

### Étape 1 — Analyse fréquentielle (estimation initiale)

`generate_frequency_mapping()`

L'algorithme calcule les fréquences des lettres dans le texte chiffré et les trie de la plus fréquente à la moins fréquente. La même opération est effectuée avec le tableau de référence des fréquences françaises. Les deux classements sont ensuite alignés :

```
chiffré (par fréq.) : r  s  h  f  e  n  ...
français (réf.) :     e  a  s  t  i  r  ...
→ correspondance :    r→e, s→a, h→s, f→t, ...
```

Il ne s'agit que d'une **estimation grossière** — les lettres aux fréquences similaires seront souvent mal associées. Cela sert de point de départ pour l'optimisation suivante. Les lettres absentes du texte chiffré sont complétées aléatoirement.

---

### Étape 2 — Évaluation (scoring)

`score_text()`

Pour évaluer une correspondance, l'algorithme calcule le score du texte déchiffré à l'aide de la **log-probabilité des n-grammes**.

Un **bigramme** est une paire de lettres adjacentes (ex. `le`, `en`, `es`). Un **trigramme** est un triplet (ex. `ent`, `que`, `les`). Chaque langue possède des n-grammes caractéristiques — en français, `le` est très fréquent (~2,2 %), tandis que `xq` est quasi-absent.

Pour chaque bigramme et trigramme du texte déchiffré, l'algorithme recherche sa fréquence de référence et calcule le logarithme naturel. Toutes les valeurs sont additionnées :

```
score = Σ w_bi · log(P(bigramme)) + Σ w_tri · log(P(trigramme))
```

Les trigrammes ont un poids double (`w_tri = 2.0`) car ils encodent davantage d'information structurelle. Les n-grammes inconnus reçoivent une petite valeur de pénalité `1e-9` au lieu de zéro (pour éviter log(0)). Un score plus élevé (moins négatif) signifie que le texte ressemble davantage au français naturel.

---

### Étape 3 — Recuit simulé (optimisation)

`simulated_annealing()`

L'objectif est de trouver la correspondance de 26 lettres ayant le score le plus élevé. L'espace de recherche contient `26! ≈ 4 × 10²⁶` possibilités — une recherche exhaustive est impossible.

L'algorithme s'inspire du processus physique du **recuit des métaux** : un métal est chauffé à haute température puis refroidi lentement. À haute température, les atomes se déplacent librement et peuvent quitter des configurations défavorables ; à basse température, ils se stabilisent dans un état optimal.

À chaque étape :

1. Deux lettres sont **échangées aléatoirement** dans la correspondance actuelle
2. Le **changement de score est calculé de manière incrémentale** (seuls les n-grammes affectés par l'échange sont recalculés)
3. Si elle est **meilleure** — elle est toujours acceptée
4. Si elle est **moins bonne** — elle est acceptée avec la probabilité `exp(Δ/T)`

La température T décroît exponentiellement :

```
T(i) = T_start · (T_end / T_start)^(i / iterations)
```

À haute T, même des solutions nettement moins bonnes sont acceptées — l'algorithme explore largement. À basse T, il se comporte comme une montée de gradient et affine les détails. L'avantage clé par rapport à la montée de gradient simple : **la capacité à s'échapper des optima locaux**.

**Scoring incrémental :** Au lieu de recalculer le score de l'ensemble du texte après chaque échange (~800 recherches de n-grammes), l'algorithme ne recalcule que les n-grammes aux positions affectées par les deux lettres échangées (~5 à 15 % du texte). Chaque itération est ainsi significativement plus rapide.

---

### Étape 4 — Redémarrages multiples

`__main__`

Le recuit simulé est non-déterministe — chaque exécution peut aboutir à une solution différente. L'ensemble du processus est donc répété `NUM_RESTARTS` fois, chacun avec une correspondance initiale aléatoire différente. Seul le résultat avec le **score le plus élevé** est conservé.

Les redémarrages multiples augmentent significativement la probabilité qu'au moins une exécution trouve l'optimum global (ou proche de l'optimum global).

---

### Étape 5 — Sauvegarde du résultat

Le meilleur texte déchiffré est :
- affiché dans la console
- sauvegardé dans `preklady/preklad_Rev2_YYYYMMDD_HHMMSS.txt`

L'horodatage dans le nom du fichier garantit que chaque exécution produit un **fichier unique** sans écraser les résultats précédents.

---

## Référence des fonctions

| Fonction | Description |
|---|---|
| `load_char_stats(filepath)` | Charge les fréquences de lettres depuis CSV ; supporte `;` et `,` |
| `load_ngram_stats(filepath)` | Charge les fréquences de bigrammes/trigrammes ; ignore les caractères accentués |
| `get_cipher_text(filepath)` | Lit le texte chiffré depuis un fichier |
| `get_text_freqs(text)` | Calcule les fréquences en pourcentage des lettres d'un texte |
| `decrypt_text(text, mapping)` | Applique une correspondance au texte en préservant la casse |
| `score_text(text, bigrams, trigrams)` | Évalue le texte par log-probabilité des bigrammes et trigrammes |
| `try_caesar(cipher_text, bigrams, trigrams)` | Teste les 25 décalages de César et retourne le meilleur |
| `generate_frequency_mapping(...)` | Crée la correspondance initiale par analyse fréquentielle |
| `precompute_cipher(cipher_text)` | Convertit le texte en tableau d'indices entiers pour un scoring rapide |
| `compute_score_delta(...)` | Calcule de manière incrémentale le changement de score pour un échange de lettres |
| `simulated_annealing(...)` | Optimise la correspondance par recuit simulé avec scoring incrémental |

---

## Paramètres ajustables

| Paramètre | Valeur par défaut | Description |
|---|---|---|
| `NUM_RESTARTS` | `50` | Nombre d'exécutions indépendantes |
| `ITERATIONS` | `100000` | Nombre d'étapes par exécution |
| `T_start` | `5.0` | Température initiale du recuit |
| `T_end` | `0.0005` | Température finale du recuit |
| `w_bi` | `1.0` | Poids des bigrammes dans le scoring |
| `w_tri` | `2.0` | Poids des trigrammes dans le scoring |
| `CAESAR_THRESHOLD` | `-500` | Seuil de score César au-dessus duquel le recuit est ignoré |

Augmenter `NUM_RESTARTS` ou `ITERATIONS` améliore la qualité du résultat au détriment du temps d'exécution. Cependant, l'amélioration la plus significative provient de **l'utilisation de tables de fréquences de n-grammes plus complètes** — voir [Constat clé](#constat-clé--la-qualité-des-données-est-déterminante).
