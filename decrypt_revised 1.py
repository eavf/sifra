import csv
import random
import math
import os

# Rozšírená tabuľka francúzskych bigramov (log-pravdepodobnosti)
FRENCH_BIGRAMS = {
    'es': 0.031, 'le': 0.026, 'en': 0.025, 'de': 0.024, 're': 0.021, 'nt': 0.019,
    'on': 0.017, 'er': 0.015, 'te': 0.015, 'el': 0.014, 'an': 0.013, 'se': 0.013,
    'it': 0.013, 'la': 0.013, 'et': 0.012, 'me': 0.012, 'ou': 0.012, 'em': 0.011,
    'ie': 0.011, 'ne': 0.011, 'ai': 0.010, 'qu': 0.010, 'il': 0.010, 'ur': 0.010,
    'sa': 0.009, 'eu': 0.009, 'ce': 0.008, 'pa': 0.008, 'ss': 0.008, 'ns': 0.008,
    'us': 0.007, 'po': 0.007, 'tr': 0.007, 'in': 0.007, 'ui': 0.006, 'ti': 0.006,
    'un': 0.006, 'is': 0.006, 've': 0.006, 'ch': 0.006, 'du': 0.005, 'da': 0.005,
    # Rozšírenie
    'ma': 0.008, 'so': 0.007, 'ro': 0.007, 'li': 0.007, 'si': 0.006, 'no': 0.006,
    'lo': 0.005, 'ra': 0.008, 'co': 0.007, 'mo': 0.005, 'al': 0.007, 'or': 0.008,
    'pl': 0.005, 'pr': 0.008, 'to': 0.006, 'oi': 0.007, 'at': 0.006, 'nd': 0.005,
    'nc': 0.004, 'ri': 0.006, 'om': 0.005, 'fr': 0.005, 'gr': 0.005, 'dr': 0.004,
    'bl': 0.003, 'br': 0.004, 'cl': 0.003, 'cr': 0.004, 'fl': 0.003, 'gl': 0.003,
    'vo': 0.004, 'oc': 0.004, 'os': 0.004, 'rs': 0.005, 'rc': 0.003, 'rm': 0.003,
    'ue': 0.008, 'au': 0.009, 'st': 0.007, 'di': 0.006, 'ge': 0.005, 'ac': 0.005,
    'ec': 0.006, 'ic': 0.004, 'uc': 0.003, 'ts': 0.004, 'ol': 0.005, 'lu': 0.005,
    'ul': 0.004, 'cu': 0.004, 'ci': 0.005, 'mi': 0.005, 'ni': 0.005, 'go': 0.004,
    'gu': 0.004, 'vi': 0.005, 'va': 0.005, 'fo': 0.004, 'fe': 0.004, 'pe': 0.007,
    'pi': 0.005, 'pu': 0.004, 'bi': 0.003, 'bo': 0.005, 'bu': 0.003,
}

# Výrazne nižšia penalizácia za neznámy bigram
MISSING_BIGRAM_SCORE = 1e-9

ALPHABET = "abcdefghijklmnopqrstuvwxyz"


def load_stats(filepath):
    """Načíta frekvencie znakov z CSV súboru (formát: znak;frekvencia)."""
    stats = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            for row in reader:
                if row and len(row) >= 2:
                    char = row[0].strip().lower()
                    try:
                        stats[char] = float(row[1].strip())
                    except ValueError:
                        continue
    except FileNotFoundError:
        print(f"Varovanie: subor '{filepath}' nebol najdeny.")
    return stats


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
    return {char: (count / total) * 100 for char, count in counts.items()}


def decrypt_text(text, mapping):
    """Aplikuje substitucne mapovanie na text (zachovava velkost pismen)."""
    res = []
    for char in text:
        key = char.lower()
        if key in mapping:
            dec_char = mapping[key]
            res.append(dec_char.upper() if char.isupper() else dec_char)
        else:
            res.append(char)
    return "".join(res)


def score_text(text):
    """Ohodnoti text pomocou log-pravdepodobnosti francuzskych bigramov."""
    score = 0.0
    clean = [c.lower() for c in text if c.isalpha()]
    for i in range(len(clean) - 1):
        bigram = clean[i] + clean[i + 1]
        score += math.log(FRENCH_BIGRAMS.get(bigram, MISSING_BIGRAM_SCORE))
    return score


def generate_frequency_mapping(cipher_text, ref_stats):
    """
    Vytvori pociatocne mapovanie zarovnanim frekvencnych tabuliek
    sifrovaného textu a referencneho jazyka.
    """
    crypt_stats = get_text_freqs(cipher_text)
    sorted_ref = sorted(ref_stats.items(), key=lambda x: x[1], reverse=True)
    sorted_crypt = sorted(crypt_stats.items(), key=lambda x: x[1], reverse=True)

    mapping = {}
    used_plain = set()

    for i in range(min(len(sorted_ref), len(sorted_crypt))):
        c_char = sorted_crypt[i][0]
        p_char = sorted_ref[i][0]
        mapping[c_char] = p_char
        used_plain.add(p_char)

    # Zvysne nenamapovane znaky pridaj nahodne
    remaining_cipher = [c for c in ALPHABET if c not in mapping]
    remaining_plain = [c for c in ALPHABET if c not in used_plain]
    random.shuffle(remaining_plain)
    for c, p in zip(remaining_cipher, remaining_plain):
        mapping[c] = p

    return mapping


def simulated_annealing(cipher_text, initial_map, iterations=40000,
                        T_start=5.0, T_end=0.005):
    """
    Simulovane zihanie (Simulated Annealing) pre hladanie optimalneho
    substitucneho kluca.

    Vyhody oproti hill-climbingu:
      - Moze uniknut z lokalnych optim prijatim horsieho riesenia
        s pravdepodobnostou exp(delta/T), ktora klesa s teplotou T
      - Vacsi pocet iteracii + viac restartov = spolahlivo lepsie vysledky

    Parametre:
        iterations : pocet krokov (odporucane: 30 000 – 80 000)
        T_start    : pociatocna teplota (vyssia = viac nahodnosti na zaciatku)
        T_end      : zaverecna teplota  (nizsia = prisnejsi vyber na konci)
    """
    current_map = initial_map.copy()
    current_score = score_text(decrypt_text(cipher_text, current_map))
    best_map = current_map.copy()
    best_score = current_score
    keys = list(current_map.keys())

    for i in range(iterations):
        # Exponencialny pokles teploty
        T = T_start * (T_end / T_start) ** (i / iterations)

        # Nahodna vymena dvoch klucov v mapovani
        k1, k2 = random.sample(keys, 2)
        new_map = current_map.copy()
        new_map[k1], new_map[k2] = new_map[k2], new_map[k1]

        new_score = score_text(decrypt_text(cipher_text, new_map))
        delta = new_score - current_score

        # Prijmi lepsie riesenie vzdy; horsie s pravdepodobnostou exp(delta/T)
        if delta > 0 or random.random() < math.exp(delta / T):
            current_map = new_map
            current_score = new_score

        if current_score > best_score:
            best_score = current_score
            best_map = current_map.copy()

    return decrypt_text(cipher_text, best_map), best_score, best_map


if __name__ == "__main__":
    cipher_text = get_cipher_text('crypt.txt')
    ref_stats = load_stats('stat.csv')

    print("Start: frekvencna analyza + simulovane zihanie...")

    best_score = float('-inf')
    best_text = ""
    best_map = {}

    NUM_RESTARTS = 20       # pocet nezavislych pokusov
    ITERATIONS = 40000      # iteracie na jeden pokus

    for attempt in range(NUM_RESTARTS):
        init_map = generate_frequency_mapping(cipher_text, ref_stats)
        decrypted, score, mapping = simulated_annealing(
            cipher_text, init_map, iterations=ITERATIONS
        )
        if score > best_score:
            best_score = score
            best_text = decrypted
            best_map = mapping
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
output_path = os.path.join(output_dir, f"preklad_Rev1_{timestamp}.txt")
 
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(best_text)
 
print(f"\nPreklad ulozeny do: {output_path}")
