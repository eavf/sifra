# Dešifrovanie substitučnej šifry — `decrypt.py`

🇸🇰 Slovensky | 🇬🇧 [English](README.md) | 🇫🇷 [Français](README.fr.md)

---

## Zadanie — o čo ide

Príklad zo strednej školy: v zadaní bol zašifrovaný text a tabuľka frekvencií jednotlivých písmen. Dalo by sa dešifrovať iba s frekvenčnou tabuľkou pre jednotlivé znaky — bez bigramov a trigramov?

Krátka odpoveď: **automaticky nie**. Frekvenčná tabuľka dáva len hrubý počiatočný odhad. Mnohé písmená majú podobné frekvencie (napr. `s`, `n`, `r`, `t`, `i` vo francúzštine všetky medzi 6–8 %), takže zoradenie nie je spoľahlivé. Čo stredoškoláci v skutočnosti robili, bola kombinácia frekvenčného odhadu s manuálnym skúšaním a jazykovou intuíciou — hádaním slov z čiastočného kontextu. Bigramy a trigramy túto intuíciu automatizujú.

Program túto metódu replikuje algoritmicky pomocou **frekvenčnej analýzy** a **simulovaného žíhania**.

---

## Substitučná šifra — o čo ide

V substitučnej šifre existuje tajný **kľúč** — tabuľka 26 dvojíc, ktorá hovorí, ktoré písmeno sa zašifruje ako ktoré:

```
plaintext:  a b c d e f g ...
ciphertext: r x k o f p q ...
```

Každé `a` v pôvodnom texte sa nahradí `r`, každé `b` sa nahradí `x` atď. Výsledný text pôsobí ako náhodný zmätok, ale **zachováva štatistické vlastnosti pôvodného jazyka** — niektoré písmená sa stále vyskytujú častejšie ako iné. Práve to umožňuje šifru prelomiť bez znalosti kľúča.

---

## Súbory projektu

| Súbor | Popis |
|---|---|
| `decrypt.py` | Hlavný skript |
| `crypt.txt` | Zašifrovaný vstupný text |
| `french_character_frequencies.csv` | Frekvencia jednotlivých písmen vo francúzštine |
| `french_bigram_frequencies.csv` | Frekvencia bigramov vo francúzštine |
| `french_trigram_frequencies.csv` | Frekvencia trigramov vo francúzštine |
| `stat.csv` | Alternatívny zdroj frekvencií (formát: `znak;frekvencia`) |
| `preklady/` | Adresár výsledkov (vytvorí sa automaticky) |

Frekvenčné tabuľky pochádzajú z [sttmedia.com](https://www.sttmedia.com/characterfrequency-french).

---

## Ako spustiť

```bash
python3 decrypt.py
```

Všetky vstupné súbory musia byť v rovnakom adresári ako skript.
Výsledok sa vypíše na konzolu a uloží do `preklady/preklad_YYYYMMDD_HHMMSS.txt`.

---

## Logika algoritmu — krok za krokom

### Krok 1 — Frekvenčná analýza (počiatočný odhad)

`generate_frequency_mapping()`

Algoritmus spočíta frekvencie písmen v šifrovanom texte a zoradí ich od najčastejšieho po najmenej časté. To isté urobí s referenčnou tabuľkou francúzskych frekvencií. Potom zarovná obe zoradenia:

```
šifra (podľa frekvencie): r  s  h  f  e  n  ...
francúzština (ref):        e  a  s  t  i  r  ...
→ počiatočné mapovanie:    r→e, s→a, h→s, f→t, ...
```

Toto je len **hrubý odhad** — písmená s podobnou frekvenciou budú často priradené nesprávne. Slúži ako štartovací bod pre ďalšiu optimalizáciu. Písmená, ktoré sa v texte nevyskytli, sa dopĺňajú náhodne.

---

### Krok 2 — Hodnotenie kvality (scoring)

`score_text()`

Na ohodnotenie mapovania algoritmus používa **log-pravdepodobnosť n-gramov**.

**Bigram** je dvojica susedných písmen (napr. `le`, `en`, `es`). **Trigram** je trojica (napr. `ent`, `que`, `les`). Každý jazyk má charakteristické n-gramy — vo francúzštine je `le` veľmi časté (~2,6 %), zatiaľ čo `xq` sa prakticky nevyskytuje.

Pre každý bigram a trigram v dešifrovanom texte sa vyhľadá jeho referenčná frekvencia a vypočíta sa prirodzený logaritmus. Všetky hodnoty sa sčítajú:

```
skóre = Σ w_bi · log(P(bigram)) + Σ w_tri · log(P(trigram))
```

Trigramy majú dvojnásobnú váhu (`w_tri = 2.0`), pretože nesú viac informácie o štruktúre jazyka. Neznáme n-gramy dostanú malú penalizačnú hodnotu `1e-9` namiesto nuly (kvôli logaritmu). Čím vyššie (menej záporné) skóre, tým viac text pripomína prirodzenú francúzštinu.

---

### Krok 3 — Simulované žíhanie (optimalizácia)

`simulated_annealing()`

Cieľom je nájsť mapovanie 26 písmen s najvyšším skóre. Priestor riešení má `26! ≈ 4 × 10²⁶` možností — vyčerpávajúce prehľadávanie je nemožné.

Algoritmus sa inšpiruje fyzikálnym procesom **žíhania kovov**: kov sa zahreje na vysokú teplotu a postupne ochladzuje. Pri vysokej teplote sa atómy pohybujú voľne a môžu opustiť nevýhodné usporiadanie; pri nízkej teplote sa usadia v stabilnom stave.

V každom kroku algoritmus:

1. Náhodne **vymení dve písmená** v aktuálnom mapovaní
2. Ohodnotí nové mapovanie pomocou `score_text()`
3. Ak je nové mapovanie **lepšie** — prijme ho vždy
4. Ak je nové mapovanie **horšie** — prijme ho s pravdepodobnosťou `exp(Δ/T)`

Teplota T sa exponenciálne znižuje počas behu:

```
T(i) = T_start · (T_end / T_start)^(i / iterations)
```

Na začiatku (vysoká T) sa prijímajú aj výrazne horšie riešenia — algoritmus exploruje. Na konci (nízka T) sa správa ako hill-climbing a dolaďuje detaily. Kľúčová výhoda oproti hill-climbingu: **schopnosť uniknúť z lokálnych optím**.

---

### Krok 4 — Viacero nezávislých pokusov (reštarty)

`__main__`

Simulované žíhanie nie je deterministické — každý beh môže skončiť inak. Celý proces sa preto opakuje `NUM_RESTARTS = 20`-krát, vždy s novým náhodným počiatočným mapovaním. Uchováva sa len výsledok s **najvyšším skóre**.

Viacero reštartov výrazne zvyšuje pravdepodobnosť, že aspoň jeden beh nájde globálne (alebo blízke globálnemu) optimum.

---

### Krok 5 — Uloženie výsledku

Najlepší dešifrovaný text sa:
- vypíše na konzolu
- uloží do `preklady/preklad_YYYYMMDD_HHMMSS.txt`

Časová pečiatka v názve súboru zaručuje, že každé spustenie vytvorí **jedinečný súbor** bez prepísania predchádzajúcich výsledkov.

---

## Prehľad funkcií

| Funkcia | Popis |
|---|---|
| `load_char_stats(filepath)` | Načíta frekvencie písmen z CSV; podporuje oddeľovače `;` aj `,` |
| `load_ngram_stats(filepath)` | Načíta bigram/trigram frekvencie; ignoruje akcentované znaky |
| `get_cipher_text(filepath)` | Načíta šifrovaný text zo súboru |
| `get_text_freqs(text)` | Spočíta percentuálne frekvencie písmen v texte |
| `decrypt_text(text, mapping)` | Aplikuje mapovanie na text, zachováva veľkosť písmen |
| `score_text(text, bigrams, trigrams)` | Ohodnotí text log-pravdepodobnosťou n-gramov |
| `generate_frequency_mapping(...)` | Vytvorí počiatočné mapovanie z frekvenčnej analýzy |
| `simulated_annealing(...)` | Optimalizuje mapovanie pomocou simulovaného žíhania |

---

## Nastaviteľné parametre

| Parameter | Predvolená hodnota | Popis |
|---|---|---|
| `NUM_RESTARTS` | `20` | Počet nezávislých pokusov |
| `ITERATIONS` | `40000` | Počet krokov žíhania na jeden pokus |
| `T_start` | `5.0` | Počiatočná teplota žíhania |
| `T_end` | `0.005` | Záverečná teplota žíhania |
| `w_bi` | `1.0` | Váha bigramov v scoring funkcii |
| `w_tri` | `2.0` | Váha trigramov v scoring funkcii |

Zvýšenie `NUM_RESTARTS` alebo `ITERATIONS` zlepší kvalitu výsledku na úkor času behu.
