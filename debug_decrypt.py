import csv
import collections

def load_stats(filepath):
    stats = {}
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
    return stats

def get_text_stats(filepath):
    counts = collections.Counter()
    total_alpha = 0
    with open(filepath, 'r', encoding='utf-8') as f:
        for char in f.read():
            if char.isalpha():
                counts[char.lower()] += 1
                total_alpha += 1
    
    stats = {}
    if total_alpha > 0:
        for char, count in counts.items():
            stats[char] = (count / total_alpha) * 100
            
    return stats

def debug(crypt_path, stat_path):
    ref_stats = load_stats(stat_path)
    crypt_stats = get_text_stats(crypt_path)

    print("Reference Stats:")
    for c, p in sorted(ref_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"{c}: {p:.2f}%")
        
    print("\nCipher Stats:")
    for c, p in sorted(crypt_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"{c}: {p:.2f}%")

    # Re-run greedy logic to show mapping
    possible_matches = []
    for c_char, c_pct in crypt_stats.items():
        for r_char, r_pct in ref_stats.items():
            diff = abs(c_pct - r_pct)
            possible_matches.append((diff, c_char, r_char))
            
    possible_matches.sort(key=lambda x: x[0])
    
    mapping = {}
    used_crypt = set()
    used_ref = set()
    
    print("\nGreedy Mapping Steps:")
    for diff, c_char, r_char in possible_matches:
        if c_char not in used_crypt and r_char not in used_ref:
            mapping[c_char] = r_char
            print(f"Mapped '{c_char}' ({crypt_stats[c_char]:.2f}%) -> '{r_char}' ({ref_stats[r_char]:.2f}%) [Diff: {diff:.4f}]")
            used_crypt.add(c_char)
            used_ref.add(r_char)

if __name__ == "__main__":
    debug('crypt.txt', 'stat.csv')
