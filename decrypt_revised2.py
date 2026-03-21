import csv
import random
import math
import os
from datetime import datetime

ALPHABET = "abcdefghijklmnopqrstuvwxyz"

# Penalizacia za neznamy n-gram
MISSING_SCORE = 1e-9


# ---------------------------------------------------------------------------
# Nacitanie frekvencii zo suborov
# ---------------------------------------------------------------------------

def load_ngram_stats(filepath):
    """
    Nacita n-gram frekvencie z CSV (format: Character/Sequence,Frequency (%)).
    Vrati slovnik { 'ab': 0.0245, ... } s hodnotami v rozsahu 0-1.
    Kluce su male pismena; ignoruju sa riadky s nealfanumerickymi znakmi
    (napr. accented chars ako 'e' ktore su mimo ASCII abecedy sifry).
    """
    stats = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # preskoc hlavicku
            for row in reader:
                if len(row) < 2:
                    continue
                seq = row[0].strip().lower()
                # Zachovaj len sekvencie zlozene z ASCII pismen (a-z)
                if not all(c in ALPHABET for c in seq):
                    continue
                try:
                    freq = float(row[1].strip().rstrip('%').strip()) / 100.0
                    if freq > 0:
                        stats[seq] = freq
                except ValueError:
                    continue
    except FileNotFoundError:
        print(f"Varovanie: subor '{filepath}' nebol najdeny.")
    return stats


def load_char_stats(filepath):
    """
    Nacita jednoznakove frekvencie.
    Podporuje oba formaty:
      - znak;frekvencia               (povodny stat.csv)
      - Character/Sequence,Frequency  (novy format zo sttmedia)
    Vrati slovnik { 'e': 15.1, ... } (hodnoty v %).
    """
    stats = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            first = f.readline()
            f.seek(0)
            delimiter = ';' if ';' in first else ','
            reader = csv.reader(f, delimiter=delimiter)
            next(reader, None)  # preskoc hlavicku
            for row in reader:
                if len(row) < 2:
                    continue
                char = row[0].strip().lower()
                if len(char) != 1 or char not in ALPHABET:
                    continue
                try:
                    freq = float(row[1].strip().rstrip('%').strip())
                    stats[char] = freq
                except ValueError:
                    continue

    except FileNotFoundError:
        print(f"Varovanie: subor '{filepath}' nebol najdeny.")
    
    print(f"Nacitane hodnoty stat:'{stats}'.")
    return stats


# ---------------------------------------------------------------------------
# Zakladne funkcie
# ---------------------------------------------------------------------------

def get_cipher_text(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def get_text_freqs(text):
    """Vrati percentualne frekvencie pismen v texte."""
    counts = {}
    total = 0
    for char in text:
        if char.isalpha():
            c = char.lower()
            counts[c] = counts.get(c, 0) + 1
            total += 1
    if total == 0:
        return {}
    return {c: (n / total) * 100 for c, n in counts.items()}


def decrypt_text(text, mapping):
    """Aplikuje substitucne mapovanie (zachovava velkost pismen)."""
    res = []
    for char in text:
        key = char.lower()
        if key in mapping:
            dec = mapping[key]
            res.append(dec.upper() if char.isupper() else dec)
        else:
            res.append(char)
    return "".join(res)


def score_text(text, bigrams, trigrams, w_bi=1.0, w_tri=2.0):
    """
    Ohodnoti text kombinaciou bigram + trigram log-pravdepodobnosti.
    Trigramy maju vyssi weight (w_tri), pretoze nesu viac informacie
    o strukture jazyka ako bigramy.
    """
    clean = [c.lower() for c in text if c.isalpha()]
    score = 0.0

    for i in range(len(clean) - 1):
        bg = clean[i] + clean[i + 1]
        score += w_bi * math.log(bigrams.get(bg, MISSING_SCORE))

    for i in range(len(clean) - 2):
        tg = clean[i] + clean[i + 1] + clean[i + 2]
        score += w_tri * math.log(trigrams.get(tg, MISSING_SCORE))

    return score


# ---------------------------------------------------------------------------
# Caesar detekcia (brute-force 25 posunov)
# ---------------------------------------------------------------------------

def try_caesar(cipher_text, bigrams, trigrams):
    """
    Vyskusa vsetkych 25 nenulových posunov (Caesar shift).
    Vrati (best_text, best_score, best_mapping, best_shift).
    Ak text nie je Caesar, vysledok bude mat nizke skore a SA ho prekoná.
    """
    best_score = float('-inf')
    best_text = ""
    best_map = {}
    best_shift = 0

    for shift in range(1, 26):
        mapping = {}
        for i in range(26):
            c = ALPHABET[i]
            p = ALPHABET[(i - shift) % 26]
            mapping[c] = p

        decrypted = decrypt_text(cipher_text, mapping)
        score = score_text(decrypted, bigrams, trigrams)

        if score > best_score:
            best_score = score
            best_text = decrypted
            best_map = mapping
            best_shift = shift

    return best_text, best_score, best_map, best_shift


# ---------------------------------------------------------------------------
# Inkrementalne skorovanie pre SA
# ---------------------------------------------------------------------------

def precompute_cipher(cipher_text):
    """
    Prekonvertuje sifrovany text na pole indexov (0-25).
    Vrati:
        indices       – list[int], len = pocet alfa znakov v texte
        positions_of  – list[list[int]], positions_of[i] = pozicie, kde
                        sa v 'indices' vyskytuje pismeno s indexom i
    """
    indices = []
    for ch in cipher_text:
        if ch.isalpha():
            indices.append(ord(ch.lower()) - ord('a'))

    # Pozicie kazdého pismena v 'indices'
    positions_of = [[] for _ in range(26)]
    for pos, idx in enumerate(indices):
        positions_of[idx].append(pos)

    return indices, positions_of


def _build_log_tables(bigrams, trigrams, w_bi=1.0, w_tri=2.0):
    """
    Predbezne vypocita log-skore pre vsetky bigramy a trigramy
    do 2D/3D poli indexovanych integermi (0-25).
    Vyhne sa opakovnemu dict.get + math.log v horúcej slucke.
    """
    log_miss = math.log(MISSING_SCORE)

    # Bigramy: bi_log[a][b] = w_bi * log(P(ab))
    bi_log = [[w_bi * log_miss] * 26 for _ in range(26)]
    for key, freq in bigrams.items():
        if len(key) == 2:
            a, b = ord(key[0]) - ord('a'), ord(key[1]) - ord('a')
            if 0 <= a < 26 and 0 <= b < 26:
                bi_log[a][b] = w_bi * math.log(freq)

    # Trigramy: tri_log[a][b][c] = w_tri * log(P(abc))
    tri_log = [[[w_tri * log_miss] * 26 for _ in range(26)] for _ in range(26)]
    for key, freq in trigrams.items():
        if len(key) == 3:
            a = ord(key[0]) - ord('a')
            b = ord(key[1]) - ord('a')
            c = ord(key[2]) - ord('a')
            if 0 <= a < 26 and 0 <= b < 26 and 0 <= c < 26:
                tri_log[a][b][c] = w_tri * math.log(freq)

    return bi_log, tri_log


def compute_full_score(indices, perm, bi_log, tri_log):
    """
    Kompletný výpočet skóre z integer-indexovaného textu.
    perm[i] = plaintext index pre cipher index i.
    """
    n = len(indices)
    score = 0.0
    # Prekonvertuj text cez mapovanie raz
    plain = [perm[c] for c in indices]

    for i in range(n - 1):
        score += bi_log[plain[i]][plain[i + 1]]
    for i in range(n - 2):
        score += tri_log[plain[i]][plain[i + 1]][plain[i + 2]]

    return score, plain


def compute_score_delta(plain, indices, perm, k1, k2,
                        positions_of, bi_log, tri_log):
    """
    Inkrementálne vypočíta zmenu skóre pri výmene perm[k1] <-> perm[k2].

    Prístup: zozbieraj unikátne štartovacie pozície bigramov a trigramov,
    ktoré obsahujú aspoň jednu pozíciu ovplyvnenú swapom.
    Každý bigram/trigram sa spracuje práve raz → žiadna korekcia duplikátov.
    """
    n = len(plain)

    # Pozície v texte, ktorých plaintext hodnota sa mení
    affected = set()
    for pos in positions_of[k1]:
        affected.add(pos)
    for pos in positions_of[k2]:
        affected.add(pos)

    if not affected:
        return 0.0

    new_p1 = perm[k2]  # po swape: perm[k1] dostane starý perm[k2]
    new_p2 = perm[k1]

    # Pomocná funkcia: nová plaintext hodnota na pozícii
    def new_plain(pos):
        ci = indices[pos]
        if ci == k1:
            return new_p1
        elif ci == k2:
            return new_p2
        else:
            return plain[pos]

    # Zozbieraj unikátne bigram ŠTART pozície (bigram = (i, i+1))
    bi_positions = set()
    for pos in affected:
        if pos > 0:
            bi_positions.add(pos - 1)  # bigram začínajúci na pos-1
        if pos < n - 1:
            bi_positions.add(pos)      # bigram začínajúci na pos

    # Zozbieraj unikátne trigram ŠTART pozície (trigram = (i, i+1, i+2))
    tri_positions = set()
    for pos in affected:
        if pos > 1:
            tri_positions.add(pos - 2)
        if pos > 0 and pos < n - 1:
            tri_positions.add(pos - 1)
        if pos < n - 2:
            tri_positions.add(pos)

    delta = 0.0

    # Bigramy: pre každú štart pozíciu odpočítaj starý, pridaj nový
    for i in bi_positions:
        old_a, old_b = plain[i], plain[i + 1]
        na, nb = new_plain(i), new_plain(i + 1)
        delta -= bi_log[old_a][old_b]
        delta += bi_log[na][nb]

    # Trigramy: pre každú štart pozíciu odpočítaj starý, pridaj nový
    for i in tri_positions:
        old_a, old_b, old_c = plain[i], plain[i + 1], plain[i + 2]
        na, nb, nc = new_plain(i), new_plain(i + 1), new_plain(i + 2)
        delta -= tri_log[old_a][old_b][old_c]
        delta += tri_log[na][nb][nc]

    return delta


# ---------------------------------------------------------------------------
# Pociatocne mapovanie (frekvencna analyza)
# ---------------------------------------------------------------------------

def generate_frequency_mapping(cipher_text, ref_stats):
    """
    Vytvori pociatocne mapovanie zarovnanim frekvencnych tabuliek
    sifrovaného textu a referencneho jazyka.
    """
    crypt_stats = get_text_freqs(cipher_text)
    sorted_ref   = sorted(ref_stats.items(), key=lambda x: x[1], reverse=True)
    sorted_crypt = sorted(crypt_stats.items(), key=lambda x: x[1], reverse=True)

    mapping   = {}
    used_plain = set()

    for i in range(min(len(sorted_ref), len(sorted_crypt))):
        c_char = sorted_crypt[i][0]
        p_char = sorted_ref[i][0]
        mapping[c_char] = p_char
        used_plain.add(p_char)

    # Zvysne nenamapovane znaky pridaj nahodne
    remaining_cipher = [c for c in ALPHABET if c not in mapping]
    remaining_plain  = [c for c in ALPHABET if c not in used_plain]
    random.shuffle(remaining_plain)
    for c, p in zip(remaining_cipher, remaining_plain):
        mapping[c] = p

    return mapping


# ---------------------------------------------------------------------------
# Simulovane zihanie (s inkrementalnym skorovanim)
# ---------------------------------------------------------------------------

def simulated_annealing(cipher_text, initial_map, bigrams, trigrams,
                        iterations=40000, T_start=5.0, T_end=0.005,
                        _precomputed=None):
    """
    Simulovane zihanie pre hladanie optimalneho substitucneho kluca.

    Oproti hill-climbingu dokaze uniknut z lokalnych optim: horsie
    riesenie je prijate s pravdepodobnostou exp(delta/T), ktora klesa
    s teplotou T (exponencialny rozvrh ochladzovania).

    Pouziva inkrementalne skorovanie: namiesto prepoctu celého textu
    pri kazdej iteracii sa menia len n-gramy na poziciach ovplyvnenych
    vymenou dvoch pismen (typicky ~8 % textu).

    Parametre:
        iterations    : pocet krokov (odporucane: 30 000 - 60 000)
        T_start       : pociatocna teplota
        T_end         : zaverecna teplota
        _precomputed  : (indices, positions_of, bi_log, tri_log) — ak je
                        None, vypocita sa; ak sa vola opakovane, posli tu
                        pre usporenie casu.
    """
    # Predvypocet (raz pre vsetky restarty)
    if _precomputed is not None:
        indices, positions_of, bi_log, tri_log = _precomputed
    else:
        indices, positions_of = precompute_cipher(cipher_text)
        bi_log, tri_log = _build_log_tables(bigrams, trigrams)

    # Permutacia: perm[cipher_index] = plaintext_index
    perm = [0] * 26
    for c_char, p_char in initial_map.items():
        perm[ord(c_char) - ord('a')] = ord(p_char) - ord('a')

    current_score, plain = compute_full_score(indices, perm, bi_log, tri_log)
    best_perm = perm[:]
    best_score = current_score

    cooling = (T_end / T_start)
    log_rand = random.random  # local lookup
    sample = random.sample
    exp = math.exp

    for i in range(iterations):
        T = T_start * cooling ** (i / iterations)

        k1, k2 = sample(range(26), 2)

        delta = compute_score_delta(
            plain, indices, perm, k1, k2, positions_of, bi_log, tri_log
        )

        if delta > 0 or log_rand() < exp(delta / T):
            # Prijmi swap
            perm[k1], perm[k2] = perm[k2], perm[k1]
            # Aktualizuj plain array
            for pos in positions_of[k1]:
                plain[pos] = perm[k1]
            for pos in positions_of[k2]:
                plain[pos] = perm[k2]
            current_score += delta

        if current_score > best_score:
            best_score = current_score
            best_perm = perm[:]

    # Rekonštrukcia najlepšieho mapovania (dict)
    best_map = {}
    for i in range(26):
        best_map[ALPHABET[i]] = ALPHABET[best_perm[i]]

    return decrypt_text(cipher_text, best_map), best_score, best_map


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Skript ocakava tieto subory v rovnakom adresari:
    #   crypt.txt                        - zasifrovany text
    #   french_character_frequencies.csv - jednoznakove frekvencie (sttmedia.com)
    #   french_bigram_frequencies.csv    - bigram frekvencie        (sttmedia.com)
    #   french_trigram_frequencies.csv   - trigram frekvencie       (sttmedia.com)
    #
    # Pre jednoznakove frekvencie je ako fallback podporovany aj povodny stat.csv.

    cipher_text = get_cipher_text('crypt.txt')

    char_file = ('french_character_frequencies.csv'
                 if os.path.exists('french_character_frequencies.csv')
                 else 'stat.csv')
    ref_stats = load_char_stats(char_file)
    bigrams   = load_ngram_stats('french_bigram_frequencies.csv')
    trigrams  = load_ngram_stats('french_trigram_frequencies.csv')

    print(f"Nacitane: {len(ref_stats)} znakov, {len(bigrams)} bigramov, {len(trigrams)} trigramov")

    # -----------------------------------------------------------------------
    # Krok 1: Caesar detekcia (okamzita, 25 pokusov)
    # -----------------------------------------------------------------------
    print("\n--- Krok 1: Caesar detekcia (25 posunov) ---")
    caesar_text, caesar_score, caesar_map, caesar_shift = try_caesar(
        cipher_text, bigrams, trigrams
    )
    print(f"Najlepsi Caesar posun: {caesar_shift}  skore = {caesar_score:.1f}")
    print(f"Prvy riadok: {caesar_text.splitlines()[0][:80]}")

    best_score = caesar_score
    best_text  = caesar_text
    best_map   = caesar_map
    method     = f"Caesar (posun {caesar_shift})"

    # -----------------------------------------------------------------------
    # Krok 2: SA (len ak Caesar nedal dost dobre skore)
    # -----------------------------------------------------------------------
    # Prah: ak je Caesar skore vyssie ako -500, je to takmer urcite spravne
    CAESAR_THRESHOLD = -500

    NUM_RESTARTS = 50
    ITERATIONS   = 100000
    T_start      = 5.0
    T_end        = 0.0005

    if caesar_score < CAESAR_THRESHOLD:
        print(f"\n--- Krok 2: Simulovane zihanie ({NUM_RESTARTS}x{ITERATIONS}) ---")

        # Predvypocet (zdielany medzi restartmi)
        indices, positions_of = precompute_cipher(cipher_text)
        bi_log, tri_log = _build_log_tables(bigrams, trigrams)
        precomp = (indices, positions_of, bi_log, tri_log)

        for attempt in range(NUM_RESTARTS):
            init_map = generate_frequency_mapping(cipher_text, ref_stats)
            decrypted, score, mapping = simulated_annealing(
                cipher_text, init_map, bigrams, trigrams,
                iterations=ITERATIONS, T_start=T_start, T_end=T_end,
                _precomputed=precomp
            )
            if score > best_score:
                best_score = score
                best_text  = decrypted
                best_map   = mapping
                method     = f"SA pokus {attempt + 1}"
                print(f"  Pokus {attempt + 1:2d}/{NUM_RESTARTS}: NOVE MAXIMUM  skore = {score:.1f}")
            else:
                print(f"  Pokus {attempt + 1:2d}/{NUM_RESTARTS}: skore = {score:.1f}")
    else:
        print("Caesar skore je dostatocne vysoke, SA preskocene.")

    print(f"\n=== Finale desifrovanie (metoda: {method}) ===")
    print(best_text)
    print(f"\nFinalne skore: {best_score:.1f}")

    # Uloz preklad do adresara 'preklady' vedla skriptu
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "preklady")
    os.makedirs(output_dir, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"preklad_Rev2_{timestamp}.txt")

    params_block = f"""
---
Parametre behu
--------------
Datum a cas:       {now.strftime("%Y-%m-%d %H:%M:%S")}
Metoda:            {method}
Vstupny subor:     crypt.txt
Frekvencny subor:  {char_file}
Caesar posun:      {caesar_shift}
Caesar skore:      {caesar_score:.1f}
Pocet restartov:   {NUM_RESTARTS}
Iteracie/restart:  {ITERATIONS}
T_start:           {T_start}
T_end:             {T_end}
Finalne skore:     {best_score:.1f}
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(best_text)
        f.write(params_block)

    print(f"\nPreklad ulozeny do: {output_path}")