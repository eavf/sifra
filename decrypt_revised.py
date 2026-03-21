import csv
import random
import math

# Extended French bigrams (log probabilities)
FRENCH_BIGRAMS = {
    'es': 0.031, 'le': 0.026, 'en': 0.025, 'de': 0.024, 're': 0.021, 'nt': 0.019,
    'on': 0.017, 'er': 0.015, 'te': 0.015, 'el': 0.014, 'an': 0.013, 'se': 0.013,
    'it': 0.013, 'la': 0.013, 'et': 0.012, 'me': 0.012, 'ou': 0.012, 'em': 0.011,
    'ie': 0.011, 'ne': 0.011, 'ai': 0.010, 'qu': 0.010, 'il': 0.010, 'ur': 0.010,
    'sa': 0.009, 'eu': 0.009, 'ce': 0.008, 'pa': 0.008, 'ss': 0.008, 'ns': 0.008,
    'us': 0.007, 'po': 0.007, 'tr': 0.007, 'in': 0.007, 'ui': 0.006, 'ti': 0.006,
    'un': 0.006, 'is': 0.006, 've': 0.006, 'ch': 0.006, 'du': 0.005, 'da': 0.005,
    # Extended entries for better French coverage
    'ma': 0.008, 'so': 0.007, 'ro': 0.007, 'li': 0.007, 'si': 0.006, 'no': 0.006,
    'lo': 0.005, 'ra': 0.008, 'co': 0.007, 'mo': 0.005, 'al': 0.007, 'or': 0.008,
    'pl': 0.005, 'pr': 0.008, 'to': 0.006, 'oi': 0.007, 'at': 0.006, 'nd': 0.005,
    'ri': 0.006, 'om': 0.005, 'nc': 0.004, 'bl': 0.003, 'br': 0.004,
    'fl': 0.003, 'fr': 0.005, 'gl': 0.003, 'gr': 0.005, 'dr': 0.004, 'cr': 0.004,
    'au': 0.009, 'ue': 0.007, 'io': 0.005, 'vo': 0.004, 'di': 0.006, 'fi': 0.004,
    'vi': 0.005, 'ni': 0.005, 'ge': 0.005, 'ci': 0.004, 'pi': 0.004, 'mi': 0.004,
    'ar': 0.007, 'ir': 0.006, 'ot': 0.005, 'ux': 0.004, 'ex': 0.004, 'oc': 0.004,
    'ac': 0.005, 'ec': 0.006, 'rs': 0.006, 'ts': 0.004, 'ls': 0.004,
}

MISSING_BIGRAM_SCORE = 1e-9
ALPHABET = "abcdefghijklmnopqrstuvwxyz"


def load_stats(filepath):
    stats = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            for row in reader:
                if row and len(row) >= 2:
                    char = row[0].strip().lower()
                    try:
                        freq = float(row[1].strip())
                        stats[char] = freq
                    except ValueError:
                        continue
    except FileNotFoundError:
        print(f"Warning: stats file '{filepath}' not found.")
    return stats


def get_cipher_text(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def get_text_freqs(text):
    counts = {}
    total = 0
    for char in text:
        if char.isalpha():
            c = char.lower()
            counts[c] = counts.get(c, 0) + 1
            total += 1
    if total > 0:
        return {char: (count / total) * 100 for char, count in counts.items()}
    return {}


def decrypt_text(text, mapping):
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
    """Score text using bigram log-probabilities. Higher = more likely French."""
    score = 0.0
    clean = [c.lower() for c in text if c.isalpha()]
    for i in range(len(clean) - 1):
        bigram = clean[i] + clean[i + 1]
        score += math.log(FRENCH_BIGRAMS.get(bigram, MISSING_BIGRAM_SCORE))
    return score


def generate_frequency_mapping(cipher_text, ref_stats):
    """Initial mapping: align cipher letters to French by descending frequency."""
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

    # Fill remaining unmapped cipher chars randomly
    remaining_cipher = [c for c in ALPHABET if c not in mapping]
    remaining_plain = [c for c in ALPHABET if c not in used_plain]
    random.shuffle(remaining_plain)
    for c, p in zip(remaining_cipher, remaining_plain):
        mapping[c] = p

    return mapping


def simulated_annealing(cipher_text, initial_map, iterations=60000,
                        T_start=5.0, T_end=0.005):
    """
    Simulated annealing: accepts worse swaps with decreasing probability.
    Much better than hill-climbing at escaping local optima.

    Fixes vs original hill_climbing():
    - Accepts worsening moves with probability exp(delta/T) -> escapes local optima
    - Exponential cooling schedule
    - Tracks global best separately from current state
    """
    current_map = initial_map.copy()
    current_score = score_text(decrypt_text(cipher_text, current_map))
    best_map = current_map.copy()
    best_score = current_score
    keys = list(current_map.keys())

    for i in range(iterations):
        # Exponential cooling: hot start (explore) -> cold end (exploit)
        T = T_start * (T_end / T_start) ** (i / iterations)

        k1, k2 = random.sample(keys, 2)
        new_map = current_map.copy()
        new_map[k1], new_map[k2] = new_map[k2], new_map[k1]

        new_score = score_text(decrypt_text(cipher_text, new_map))
        delta = new_score - current_score

        # Always accept improvements; accept degradation with Boltzmann probability
        if delta > 0 or random.random() < math.exp(delta / T):
            current_map = new_map
            current_score = new_score

        if current_score > best_score:
            best_score = current_score
            best_map = current_map.copy()

    return decrypt_text(cipher_text, best_map), best_score, best_map


if __name__ == "__main__":
    text = get_cipher_text('crypt.txt')
    ref_stats = load_stats('stat.csv')

    best_score = float('-inf')
    best_text = ""

    # KEY FIXES vs original:
    # 1. Simulated annealing instead of pure hill-climbing (escapes local optima)
    # 2. Many more restarts: 30 instead of 5
    # 3. More iterations per restart: 60000 instead of 5000
    # 4. Extended bigram table (more French pairs covered)
    # 5. Stricter MISSING_BIGRAM_SCORE penalty (1e-9 vs 1e-6)
    NUM_RESTARTS = 30
    ITERATIONS = 60000

    print(f"Running {NUM_RESTARTS} restarts x {ITERATIONS} SA iterations...")
    for attempt in range(NUM_RESTARTS):
        start_map = generate_frequency_mapping(text, ref_stats)
        decrypted, score, _ = simulated_annealing(
            text, start_map, iterations=ITERATIONS
        )
        if score > best_score:
            best_score = score
            best_text = decrypted
            print(f"  Attempt {attempt + 1:>2}: NEW BEST  score = {score:.2f}")
        else:
            print(f"  Attempt {attempt + 1:>2}: score = {score:.2f}")

    print("\n=== Final Decryption ===")
    print(best_text)
    print(f"\nFinal score: {best_score:.2f}")