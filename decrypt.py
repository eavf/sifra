import csv
import collections
import random
import math
import sys

# Common French bigrams (approximate log probabilities)
# Source: standard frequency tables for French
FRENCH_BIGRAMS = {
    'es': 0.031, 'le': 0.026, 'en': 0.025, 'de': 0.024, 're': 0.021, 'nt': 0.019,
    'on': 0.017, 'er': 0.015, 'te': 0.015, 'el': 0.014, 'an': 0.013, 'se': 0.013,
    'it': 0.013, 'la': 0.013, 'et': 0.012, 'me': 0.012, 'ou': 0.012, 'em': 0.011,
    'ie': 0.011, 'ne': 0.011, 'ai': 0.010, 'qu': 0.010, 'il': 0.010, 'ur': 0.010,
    'sa': 0.009, 'eu': 0.009, 'ce': 0.008, 'pa': 0.008, 'ss': 0.008, 'ns': 0.008,
    'us': 0.007, 'po': 0.007, 'tr': 0.007, 'in': 0.007, 'ui': 0.006, 'ti': 0.006,
    'un': 0.006, 'is': 0.006, 've': 0.006, 'ch': 0.006, 'du': 0.005, 'da': 0.005
}

MISSING_BIGRAM_SCORE = 1e-6
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
        # Fallback if file missing
        pass
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
    stats = {}
    if total > 0:
        for char, count in counts.items():
            stats[char] = (float(count) / total) * 100
    return stats

def decrypt_text(text, mapping):
    res = []
    for char in text:
        key = char.lower()
        if key in mapping:
            dec_char = mapping[key]
            if char.isupper():
                res.append(dec_char.upper())
            else:
                res.append(dec_char)
        else:
            res.append(char)
    return "".join(res)

def score_text(text):
    score = 0.0
    clean_text = "".join([c.lower() for c in text if c.isalpha()])
    for i in range(len(clean_text) - 1):
        bigram = clean_text[i:i+2]
        prob = FRENCH_BIGRAMS.get(bigram, MISSING_BIGRAM_SCORE)
        score += math.log(prob)
    return score

def generate_frequency_mapping(cipher_text, ref_stats):
    """Generates an initial mapping based on single-letter frequency."""
    crypt_stats = get_text_freqs(cipher_text)
    
    # Sort both by freq
    sorted_ref = sorted(ref_stats.items(), key=lambda x: x[1], reverse=True)
    sorted_crypt = sorted(crypt_stats.items(), key=lambda x: x[1], reverse=True)
    
    mapping = {}
    # Basic alignment
    # Note: lengths might differ, so be careful
    
    # Fill mapping with best guesses
    used_cipher = set()
    used_plain = set()
    
    # 1. Map top frequent chars
    for i in range(min(len(sorted_ref), len(sorted_crypt))):
        c_char = sorted_crypt[i][0]
        p_char = sorted_ref[i][0]
        mapping[c_char] = p_char
        used_cipher.add(c_char)
        used_plain.add(p_char)
        
    # 2. Fill remaining unmapped cipher chars with random remaining plain chars
    remaining_cipher = [c for c in ALPHABET if c not in used_cipher]
    remaining_plain = [c for c in ALPHABET if c not in used_plain]
    random.shuffle(remaining_plain)
    
    for c, p in zip(remaining_cipher, remaining_plain):
        mapping[c] = p
        
    return mapping

def hill_climbing(cipher_text, initial_map, iterations=5000):
    current_map = initial_map.copy()
    current_decryption = decrypt_text(cipher_text, current_map)
    current_score = score_text(current_decryption)
    keys = list(current_map.keys())
    
    for i in range(iterations):
        k1, k2 = random.sample(keys, 2)
        new_map = current_map.copy()
        new_map[k1], new_map[k2] = new_map[k2], new_map[k1]
        
        new_decryption = decrypt_text(cipher_text, new_map)
        new_score = score_text(new_decryption)
        
        if new_score > current_score:
            current_score = new_score
            current_map = new_map

    return decrypt_text(cipher_text, current_map), current_score

if __name__ == "__main__":
    text = get_cipher_text('crypt.txt')
    ref_stats = load_stats('stat.csv')
    print(ref_stats)
    
    # Start with frequency analysis as the baseline
    start_map = generate_frequency_mapping(text, ref_stats)
    
    best_text = decrypt_text(text, start_map)
    best_score = score_text(best_text)
    print(f"Initial Greedy Score: {best_score}")
    
    # Hill Climb from this good starting point
    # We don't need many restarts if the start is good, but let's do a few
    for attempt in range(5):
        print(f"Refining attempt {attempt+1}...")
        decrypted, score = hill_climbing(text, start_map, iterations=5000)
        
        if score > best_score:
            best_score = score
            best_text = decrypted
            
    print("\n=== Final Decryption ===")
    print(best_text)

