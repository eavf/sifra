## Zadanie — o čo ide
Tu je príklad zo strednej školy, kde v zadaní bolo :
* zašifrovaný text
* tabuľku s frekvenciou jednotlivých písmen
Základná otázka je či by bolo by možné dešifrovať ten text iba s frekvenčnou tabuľkou pre jednotlivé znaky, bez použitia bigramov a trigramov?

Riešenie iba z frekvenčnou tabuľkou na jednotlivé znaky nie je moc možné ako samostatný algoritmus. Áno, bolo by to možné — ale s dôležitým "ale".

**Samotná frekvenčná tabuľka nestačí na automatické dešifrovanie.** Dá sa ňou získať len **počiatočný odhad** mapovania (zoradí písmená šifrovaného textu podľa frekvencie a priradíš ich k písmenám referenčného jazyka). Problém je, že frekvencie mnohých písmen sú si veľmi blízke — napríklad `s`, `n`, `r`, `t`, `i` sú vo francúzštine všetky medzi 6–8 %, takže poradie nie je spoľahlivé a počiatočný odhad bude mať niekoľko zámien.

**Čo teda stredoškoláci v skutočnosti robili?** Frekvenčná tabuľka dáva len odrazový mostík — zorientovanie sa. Potom **manuálne skúšanie** a opravovanie: pozreť sa na čiastočne dešifrovaný text, uhádnuť konkrétne slovo podľa kontextu (napr. `_e` → `le`, trojpísmenové slovo s vysokou frekvenciou → `les` alebo `des`), a postupne opravovať mapovanie. To je práve tá "ručná" kryptoanalýza — kombinácia štatistiky a jazykového úsudku.

**Algoritmus bez bigramov by teda musel robiť to isté** — iba frekvenčné zoradenie dá skóre, podľa ktorého nevieme povedať či je výsledok správny alebo nie. Bigramy a trigramy sú v podstate *automatizácia toho jazykového úsudku* — nahrádzajú "aha, toto vyzerá ako francúzske slovo" matematickým skóre.

Takže záver: na strednej škole to bolo **možné preto, lebo to robil človek** s jazykovou intuíciou. Pre počítačový algoritmus bez bigramov by frekvenčná tabuľka nestačila — skončil by v lokálnom optime bez schopnosti rozpoznať, či sa blíži k správnemu riešeniu.

# Dešifrovanie substitučnej šifry — `decrypt.py`

Program automaticky dešifruje text zašifrovaný **jednoduchou substitučnou šifrou**
(monoalfabetická substitúcia), kde každé písmeno abecedy bolo nahradené iným písmenom.
Využíva kombináciu frekvenčnej analýzy a simulovaného žíhania.

---

## Substitučná šifra — o čo ide

V substitučnej šifre existuje tajný **kľúč** — tabuľka 26 dvojíc, ktorá hovorí,
ktoré písmeno sa zašifruje ako ktoré. Napríklad:

```
plaintext:  a b c d e f g ...
ciphertext: r x k o f p q ...
```

Každé `a` v pôvodnom texte sa nahradí `r`, každé `b` sa nahradí `x` atď.
Výsledný zašifrovaný text pôsobí ako náhodný zmätok, ale **zachováva štatistické
vlastnosti pôvodného jazyka** — niektoré písmená sa stále vyskytujú častejšie ako iné.
Práve to umožňuje šifru prelomiť bez znalosti kľúča.

---

## Súbory projektu

| Súbor | Popis |
|---|---|
| `decrypt.py` | Hlavný skript |
| `crypt.txt` | Zašifrovaný vstupný text |
| `french_character_frequencies.csv` | Frekvencia jednotlivých písmen vo francúzštine |
| `french_bigram_frequencies.csv` | Frekvencia dvojíc písmen (bigramov) vo francúzštine |
| `french_trigram_frequencies.csv` | Frekvencia trojíc písmen (trigramov) vo francúzštine |
| `stat.csv` | Alternatívny zdroj frekvencií písmen (pôvodný formát `znak;frekvencia`) |
| `preklady/` | Adresár, do ktorého sa ukladajú výsledky (vytvorí sa automaticky) |

Frekvenčné tabuľky pochádzajú z [sttmedia.com](https://www.sttmedia.com/characterfrequency-french).

---

## Ako spustiť

```bash
python3 decrypt.py
```

Všetky vstupné súbory musia byť v rovnakom adresári ako skript.
Výsledok sa vypíše na konzolu a zároveň uloží do `preklady/preklad_YYYYMMDD_HHMMSS.txt`.

---

## Logika algoritmu — krok za krokom

### Krok 1 — Frekvenčná analýza (počiatočný odhad)

Funkcia `generate_frequency_mapping()`

Algoritmus si najprv spočíta, ako často sa vyskytuje každé písmeno
v zašifrovanom texte, a výsledok zoradí od najčastejšieho po najmenej časté.
To isté urobí s referenčnou tabuľkou francúzskych frekvencií.
Potom jednoducho zarovná obe zoradenia — najčastejšie šifrované písmeno
priradí k najčastejšiemu francúzskemu písmenu atď.

```
šifra (podľa frekvencie): r  s  h  f  e  n  ...
francúzština (ref):        e  a  s  t  i  r  ...
→ počiatočné mapovanie:    r→e, s→a, h→s, f→t, ...
```

Toto mapovanie je len **hrubý odhad** — mnohé písmená s podobnou frekvenciou
budú priradené nesprávne. Slúži ale ako dobrý štartovací bod pre ďalšiu optimalizáciu.
Zvyšné písmená, ktoré sa v texte vôbec nevyskytli, sa dopĺňajú náhodne.

---

### Krok 2 — Hodnotenie kvality (scoring)

Funkcia `score_text()`

Aby algoritmus vedel, či je nejaké mapovanie dobré alebo zlé, potrebuje spôsob,
ako ohodnotiť dešifrovaný text. Používa na to **log-pravdepodobnosť n-gramov**.

**Bigram** je dvojica susedných písmen (napr. `le`, `en`, `es`).
**Trigram** je trojica (napr. `ent`, `que`, `les`).
Pre každý jazyk existujú charakteristické bigramy a trigramy — vo francúzštine
je napríklad `le` veľmi časté (2.6 %), zatiaľ čo `xq` sa prakticky nevyskytuje.

Pre každý bigram a trigram v dešifrovanom texte sa vyhľadá jeho frekvencia
v referenčnej tabuľke a vypočíta sa prirodzený logaritmus. Všetky hodnoty
sa sčítajú do jedného skóre:

```
skóre = Σ w_bi · log(P(bigram)) + Σ w_tri · log(P(trigram))
```

Trigramy majú dvojnásobnú váhu (`w_tri = 2.0`), pretože nesú viac informácie
o štruktúre jazyka. Čím vyššie (menej záporné) skóre, tým viac text
pripomína prirodzený francúzsky jazyk. Neznáme n-gramy dostanú malú
penalizačnú hodnotu `1e-9` namiesto nuly (kvôli logaritmu).

---

### Krok 3 — Simulované žíhanie (optimalizácia)

Funkcia `simulated_annealing()`

Toto je jadro celého algoritmu. Cieľom je nájsť také mapovanie 26 písmen,
ktoré dá najvyššie skóre. Problém je, že existuje `26! ≈ 4 × 10²⁶` možných
mapovaní — prehľadanie všetkých je nemožné.

Algoritmus sa inšpiruje fyzikálnym procesom **žíhania kovov**: kov sa zahreje
na vysokú teplotu a postupne ochladzuje. Pri vysokej teplote sa atómy pohybujú
náhodne a môžu opustiť nevýhodné usporiadanie; pri nízkej teplote sa usadia
v stabilnom (ideálne globálne optimálnom) stave.

V každom kroku algoritmus:

1. Náhodne **vymení dve písmená** v aktuálnom mapovaní (napr. prehodí `r→e` a `s→a` na `r→a` a `s→e`)
2. Ohodnotí nové mapovanie pomocou `score_text()`
3. Ak je nové mapovanie **lepšie** — prijme ho vždy
4. Ak je nové mapovanie **horšie** — prijme ho s pravdepodobnosťou `exp(Δ/T)`

Pravdepodobnosť prijatia horšieho riešenia závisí od **teploty T**, ktorá
sa exponenciálne znižuje počas behu:

```
T(i) = T_start · (T_end / T_start)^(i / iterations)
```

Na začiatku (vysoká T) sa prijímajú aj výrazne horšie riešenia — algoritmus
„blúdi" po priestore riešení a hľadá sľubné oblasti. Na konci (nízka T)
sa správa takmer ako hill-climbing a dolaďuje detaily.

Toto je kľúčová výhoda oproti jednoduchému hill-climbingu: **schopnosť
uniknúť z lokálnych optím**.

---

### Krok 4 — Viacero nezávislých pokusov (reštarty)

Hlavný blok `__main__`

Simulované žíhanie nie je deterministické — pri každom spustení môže
skončiť na inom riešení. Preto sa celý proces opakuje `NUM_RESTARTS = 20`-krát,
vždy s novým náhodným počiatočným mapovaním. Z všetkých pokusov sa uchováva
len ten s **najvyšším skóre**.

Viacero reštartov výrazne zvyšuje pravdepodobnosť, že aspoň jeden pokus
nájde globálne (alebo blízke globálnemu) optimum.

---

### Krok 5 — Uloženie výsledku

Po skončení všetkých pokusov sa najlepší dešifrovaný text:
- vypíše na konzolu
- uloží do súboru `preklady/preklad_YYYYMMDD_HHMMSS.txt` vedľa skriptu

Časová pečiatka v názve súboru zaručuje, že každé spustenie vytvorí
**jedinečný súbor** a neprepíše predchádzajúce výsledky.

---

## Prehľad funkcií

| Funkcia | Popis |
|---|---|
| `load_char_stats(filepath)` | Načíta frekvencie písmen z CSV; podporuje formát `;` aj `,` |
| `load_ngram_stats(filepath)` | Načíta bigram/trigram frekvencie z CSV; ignoruje akcentované znaky |
| `get_cipher_text(filepath)` | Načíta zašifrovaný text zo súboru |
| `get_text_freqs(text)` | Spočíta percentuálne frekvencie písmen v texte |
| `decrypt_text(text, mapping)` | Aplikuje mapovanie na text, zachováva veľkosť písmen |
| `score_text(text, bigrams, trigrams)` | Ohodnotí text log-pravdepodobnosťou bigramov a trigramov |
| `generate_frequency_mapping(cipher_text, ref_stats)` | Vytvorí počiatočné mapovanie podľa frekvenčnej analýzy |
| `simulated_annealing(...)` | Optimalizuje mapovanie pomocou simulovaného žíhania |

---

## Nastaviteľné parametre

V hlavnom bloku skriptu možno upraviť:

| Parameter | Predvolená hodnota | Popis |
|---|---|---|
| `NUM_RESTARTS` | `20` | Počet nezávislých pokusov |
| `ITERATIONS` | `40000` | Počet krokov simulovaného žíhania na jeden pokus |
| `T_start` | `5.0` | Počiatočná teplota žíhania |
| `T_end` | `0.005` | Záverečná teplota žíhania |
| `w_bi` | `1.0` | Váha bigramov v scoring funkcii |
| `w_tri` | `2.0` | Váha trigramov v scoring funkcii |

Zvýšenie `NUM_RESTARTS` alebo `ITERATIONS` zlepší kvalitu výsledku na úkor času behu.