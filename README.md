# Substitution Cipher Decryption — `decrypt_revised2.py`

🇸🇰 [Slovensky](README.sk.md) | 🇬🇧 English | 🇫🇷 [Français](README.fr.md)

---

## Background — What Is This About?

A classic high school exercise: given a ciphertext and a table of letter frequencies, can it be decrypted using only single-character frequencies — without bigrams or trigrams?

The short answer: **not automatically**. A frequency table alone gives only a rough initial guess. Many letters share similar frequencies (e.g. `s`, `n`, `r`, `t`, `i` in French all fall between 6–8 %), so the ordering is unreliable. What students actually did was combine the frequency hint with manual trial-and-error and linguistic intuition — guessing words from partial context. Bigrams and trigrams automate exactly that intuition.

This program replicates that process algorithmically, using **frequency analysis** combined with **simulated annealing**.

---

## Key Insight — Data Quality Matters Most

The single most important factor for decryption quality is **the size and accuracy of the n-gram frequency tables**. A first version using only ~40 bigrams and ~50 trigrams produced garbled text; expanding the tables to **~250 bigrams and ~100 trigrams** immediately produced near-perfect decryption — a far bigger improvement than any algorithmic tuning (more restarts, more iterations, trigram weights, etc.).

The scoring function can only distinguish good French from bad French if it has enough reference data. With too few n-grams, almost every letter pair receives the same penalty, and the algorithm cannot navigate toward the correct solution.

---

## What Is a Substitution Cipher?

A substitution cipher uses a secret **key** — a table of 26 pairs mapping each plaintext letter to a ciphertext letter:

```
plaintext:  a b c d e f g ...
ciphertext: r x k o f p q ...
```

Every `a` becomes `r`, every `b` becomes `x`, etc. The result looks random, but it **preserves the statistical properties of the original language** — some letters still appear more often than others. That is exactly what allows breaking the cipher without knowing the key.

---

## Project Files

| File | Description |
|---|---|
| `decrypt_revised2.py` | Main script |
| `crypt.txt` | Encrypted input text |
| `french_character_frequencies.csv` | French single-letter frequencies (26 letters) |
| `french_bigram_frequencies.csv` | French bigram frequencies (~250 pairs) |
| `french_trigram_frequencies.csv` | French trigram frequencies (~100 triples) |
| `stat.csv` | Alternative frequency source (format: `char;frequency`) |
| `preklady/` | Output directory for results (created automatically) |
| `test/` | Test suite |

Frequency tables sourced from [sttmedia.com](https://www.sttmedia.com/characterfrequency-french) and expanded for better coverage.

---

## How to Run

```bash
python3 decrypt_revised2.py
```

All input files must be in the same directory as the script.
The result is printed to the console and saved to `preklady/preklad_Rev2_YYYYMMDD_HHMMSS.txt`.

---

## Algorithm — Step by Step

### Step 0 — Caesar Detection (Pre-check)

`try_caesar()`

Before launching the expensive simulated annealing, the algorithm tests all 25 possible Caesar shifts. A Caesar cipher maps every letter by the same fixed offset (e.g. every letter shifted by 4). If the best Caesar shift produces a high score, the result is used directly and simulated annealing is skipped entirely.

For general substitution ciphers (where each letter has an independent mapping), the Caesar scores will be very low and the algorithm proceeds to the full optimisation.

---

### Step 1 — Frequency Analysis (Initial Guess)

`generate_frequency_mapping()`

Letter frequencies in the ciphertext are computed and sorted from most to least frequent. The same is done for the French reference table. The two sorted lists are aligned — the most frequent cipher letter is mapped to the most frequent French letter, and so on.

```
cipher (by freq):  r  s  h  f  e  n  ...
French (ref):      e  a  s  t  i  r  ...
→ initial mapping: r→e, s→a, h→s, f→t, ...
```

This is only a **rough estimate** — letters with similar frequencies will often be misassigned. It serves as a starting point for the next stage. Letters absent from the ciphertext are filled in randomly.

---

### Step 2 — Scoring

`score_text()`

To evaluate a mapping, the algorithm scores the decrypted text using **log-probability of n-grams**.

A **bigram** is a pair of adjacent letters (e.g. `le`, `en`, `es`). A **trigram** is a triple (e.g. `ent`, `que`, `les`). Each language has characteristic n-grams — in French, `le` is very common (~2.2 %), while `xq` is virtually absent.

For each bigram and trigram in the decrypted text, the algorithm looks up its reference frequency and takes the natural logarithm. All values are summed:

```
score = Σ w_bi · log(P(bigram)) + Σ w_tri · log(P(trigram))
```

Trigrams carry double weight (`w_tri = 2.0`) because they encode more structural information. Unknown n-grams receive a small penalty `1e-9` instead of zero (to avoid log(0)). A higher (less negative) score means the text more closely resembles natural French.

---

### Step 3 — Simulated Annealing (Optimisation)

`simulated_annealing()`

The goal is to find the 26-letter mapping with the highest score. The search space has `26! ≈ 4 × 10²⁶` possibilities — exhaustive search is impossible.

The algorithm is inspired by the physical process of **annealing metals**: a metal is heated to a high temperature and slowly cooled. At high temperature, atoms move freely and can escape unfavourable arrangements; at low temperature, they settle into a stable (ideally globally optimal) state.

At each step:

1. Randomly **swap two letters** in the current mapping
2. Compute the **score delta** incrementally (only n-grams affected by the swap are recalculated)
3. If the new mapping is **better** — always accept it
4. If the new mapping is **worse** — accept it with probability `exp(Δ/T)`

The probability of accepting a worse solution depends on **temperature T**, which decreases exponentially:

```
T(i) = T_start · (T_end / T_start)^(i / iterations)
```

At high T, even much worse solutions are accepted — the algorithm explores broadly. At low T, it behaves like hill-climbing and refines the details. This is the key advantage over plain hill-climbing: **the ability to escape local optima**.

**Incremental scoring:** Instead of rescoring the entire text after every swap (~800 n-gram lookups), the algorithm only recalculates the n-grams at positions affected by the two swapped letters (~5–15 % of the text). This makes each iteration significantly faster.

---

### Step 4 — Multiple Restarts

`__main__`

Simulated annealing is non-deterministic — each run may end at a different solution. The entire process is therefore repeated `NUM_RESTARTS` times, each with a fresh random starting mapping. Only the result with the **highest score** is kept.

Multiple restarts significantly increase the probability that at least one run finds the global (or near-global) optimum.

---

### Step 5 — Saving the Result

The best decrypted text is:
- printed to the console
- saved to `preklady/preklad_Rev2_YYYYMMDD_HHMMSS.txt`

The timestamp in the filename ensures every run produces a **unique file** without overwriting previous results.

---

## Function Reference

| Function | Description |
|---|---|
| `load_char_stats(filepath)` | Loads letter frequencies from CSV; supports `;` and `,` separators |
| `load_ngram_stats(filepath)` | Loads bigram/trigram frequencies; skips accented characters |
| `get_cipher_text(filepath)` | Reads the ciphertext from file |
| `get_text_freqs(text)` | Computes percentage letter frequencies in a text |
| `decrypt_text(text, mapping)` | Applies a mapping to text, preserving case |
| `score_text(text, bigrams, trigrams)` | Scores text by log-probability of bigrams and trigrams |
| `try_caesar(cipher_text, bigrams, trigrams)` | Tests all 25 Caesar shifts and returns the best |
| `generate_frequency_mapping(...)` | Creates initial mapping from frequency analysis |
| `precompute_cipher(cipher_text)` | Converts text to integer index array for fast scoring |
| `compute_score_delta(...)` | Incrementally computes score change for a letter swap |
| `simulated_annealing(...)` | Optimises the mapping using simulated annealing with incremental scoring |

---

## Tunable Parameters

| Parameter | Default | Description |
|---|---|---|
| `NUM_RESTARTS` | `50` | Number of independent runs |
| `ITERATIONS` | `100000` | Steps per annealing run |
| `T_start` | `5.0` | Initial annealing temperature |
| `T_end` | `0.0005` | Final annealing temperature |
| `w_bi` | `1.0` | Bigram weight in scoring |
| `w_tri` | `2.0` | Trigram weight in scoring |
| `CAESAR_THRESHOLD` | `-500` | Caesar score above which SA is skipped |

Increasing `NUM_RESTARTS` or `ITERATIONS` improves result quality at the cost of runtime. However, the most impactful improvement is **using comprehensive n-gram frequency tables** — see [Key Insight](#key-insight--data-quality-matters-most).
