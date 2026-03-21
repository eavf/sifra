import csv
import random
import math
import os

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
    Trigramy maju vyssi weight (w_tri), pretoze nesу viac informacie
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
# Simulovane zihanie
# ---------------------------------------------------------------------------

def simulated_annealing(cipher_text, initial_map, bigrams, trigrams,
                        iterations=40000, T_start=5.0, T_end=0.005):
    """
    Simulovane zihanie pre hladanie optimalneho substitucneho kluca.

    Oproti hill-climbingu dokaze uniknut z lokalnych optim: horsie
    riesenie je prijate s pravdepodobnostou exp(delta/T), ktora klesa
    s teplotou T (exponencialny rozvrh ochladzovania).

    Parametre:
        iterations : pocet krokov (odporucane: 30 000 - 60 000)
        T_start    : pociatocna teplota
        T_end      : zaverecna teplota
    """
    current_map   = initial_map.copy()
    current_score = score_text(decrypt_text(cipher_text, current_map), bigrams, trigrams)
    best_map   = current_map.copy()
    best_score = current_score
    keys = list(current_map.keys())

    for i in range(iterations):
        T = T_start * (T_end / T_start) ** (i / iterations)

        k1, k2 = random.sample(keys, 2)
        new_map = current_map.copy()
        new_map[k1], new_map[k2] = new_map[k2], new_map[k1]

        new_score = score_text(decrypt_text(cipher_text, new_map), bigrams, trigrams)
        delta = new_score - current_score

        if delta > 0 or random.random() < math.exp(delta / T):
            current_map   = new_map
            current_score = new_score

        if current_score > best_score:
            best_score = current_score
            best_map   = current_map.copy()

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
    print("Start: frekvencna analyza + simulovane zihanie...\n")

    best_score = float('-inf')
    best_text  = ""
    best_map   = {}

    NUM_RESTARTS = 20
    ITERATIONS   = 40000

    for attempt in range(NUM_RESTARTS):
        init_map = generate_frequency_mapping(cipher_text, ref_stats)
        decrypted, score, mapping = simulated_annealing(
            cipher_text, init_map, bigrams, trigrams, iterations=ITERATIONS
        )
        if score > best_score:
            best_score = score
            best_text  = decrypted
            best_map   = mapping
            print(f"  Pokus {attempt + 1:2d}/{NUM_RESTARTS}: NOVE MAXIMUM  skore = {score:.1f}")
        else:
            print(f"  Pokus {attempt + 1:2d}/{NUM_RESTARTS}: skore = {score:.1f}")

    print("\n=== Finale desifrovanie ===")
    print(best_text)
    print(f"\nFinalne skore: {best_score:.1f}")

# Uloz preklad do adresara 'preklady' vedla skriptu, s jedinecnym nazvom suboru
script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, "preklady")
os.makedirs(output_dir, exist_ok=True)
 
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = os.path.join(output_dir, f"preklad_Rev2_{timestamp}.txt")
 
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(best_text)
 
print(f"\nPreklad ulozeny do: {output_path}")