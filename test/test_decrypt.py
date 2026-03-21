"""
Testy pre decrypt_revised2.py:
  1. Caesar detekcia — overenie ze sa spusti a vrati vysledok
     (crypt.txt NIE je Caesar sifra, takze skore bude nizke)
  2. Inkrementalne skorovanie — delta sa zhoduje s plnym prepoctom
  3. SA end-to-end — kratky beh overuje ze SA produkuje lepsie skore
"""
import sys
import os
import random

# Pridaj project root do sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from decrypt_revised2 import (
    ALPHABET,
    load_ngram_stats, load_char_stats, get_cipher_text,
    decrypt_text, score_text, try_caesar,
    precompute_cipher, _build_log_tables,
    compute_full_score, compute_score_delta,
    generate_frequency_mapping, simulated_annealing,
)


def test_caesar():
    """Caesar detekcia — vyberie najlepsi posun z 25.
    crypt.txt je vseobecna substitucna sifra, nie Caesar,
    takze skore by malo byt velmi nizke (< -500)."""
    print("=== Test 1: Caesar detekcia ===")
    bigrams  = load_ngram_stats('french_bigram_frequencies.csv')
    trigrams = load_ngram_stats('french_trigram_frequencies.csv')
    cipher   = get_cipher_text('crypt.txt')

    text, score, mapping, shift = try_caesar(cipher, bigrams, trigrams)
    print(f"  Posun: {shift}  skore: {score:.1f}")
    print(f"  Prvy riadok: {text.splitlines()[0][:60]}...")

    # Overenie: vrati tuple so 4 hodnotami
    assert isinstance(shift, int) and 1 <= shift <= 25
    assert isinstance(score, float)
    assert len(mapping) == 26
    # Pre ne-Caesar text: skore by malo byt hlboko zaporne
    assert score < -500, f"Neoakavane vysoke Caesar skore: {score}"
    print("  ✓ PASSED (spravne identifikovane ako ne-Caesar)\n")


def test_incremental_scoring():
    """Porovnanie inkrementalneho delta vs plny prepocet."""
    print("=== Test 2: Inkrementalne skorovanie ===")
    bigrams  = load_ngram_stats('french_bigram_frequencies.csv')
    trigrams = load_ngram_stats('french_trigram_frequencies.csv')
    cipher   = get_cipher_text('crypt.txt')
    ref      = load_char_stats('french_character_frequencies.csv')

    indices, positions_of = precompute_cipher(cipher)
    bi_log, tri_log = _build_log_tables(bigrams, trigrams)

    random.seed(42)
    init_map = generate_frequency_mapping(cipher, ref)

    perm = [0] * 26
    for c, p in init_map.items():
        perm[ord(c) - ord('a')] = ord(p) - ord('a')

    current_score, plain = compute_full_score(indices, perm, bi_log, tri_log)
    errors = 0
    max_err = 0.0

    N_TRIALS = 200
    for trial in range(N_TRIALS):
        k1, k2 = random.sample(range(26), 2)

        delta = compute_score_delta(
            plain, indices, perm, k1, k2, positions_of, bi_log, tri_log
        )

        # Plny prepocet
        new_perm = perm[:]
        new_perm[k1], new_perm[k2] = new_perm[k2], new_perm[k1]
        new_score, _ = compute_full_score(indices, new_perm, bi_log, tri_log)
        expected = new_score - current_score

        err = abs(delta - expected)
        max_err = max(max_err, err)
        if err > 1e-6:
            errors += 1
            if errors <= 3:
                print(f"  CHYBA #{trial}: delta={delta:.6f} expected={expected:.6f} err={err:.9f}")

        # Aplikuj swap s 50% sancou (aby sa stav menial)
        if random.random() > 0.5:
            perm[k1], perm[k2] = perm[k2], perm[k1]
            for pos in positions_of[k1]:
                plain[pos] = perm[k1]
            for pos in positions_of[k2]:
                plain[pos] = perm[k2]
            current_score += delta

    print(f"  Max error: {max_err:.10f}")
    print(f"  Chyby (>1e-6): {errors}/{N_TRIALS}")
    assert errors == 0, f"Inkrementalne skorovanie ma {errors} chyb!"
    print("  ✓ PASSED\n")


def test_sa_short():
    """Kratky SA beh — overuje ze SA produkuje lepsie skore nez nahodne."""
    print("=== Test 3: SA kratky beh ===")
    bigrams  = load_ngram_stats('french_bigram_frequencies.csv')
    trigrams = load_ngram_stats('french_trigram_frequencies.csv')
    cipher   = get_cipher_text('crypt.txt')
    ref      = load_char_stats('french_character_frequencies.csv')

    init_map = generate_frequency_mapping(cipher, ref)
    initial_text = decrypt_text(cipher, init_map)
    initial_score = score_text(initial_text, bigrams, trigrams)

    # Kratky SA: 5000 iteracii, 1 restart
    decrypted, sa_score, sa_map = simulated_annealing(
        cipher, init_map, bigrams, trigrams, iterations=5000
    )
    print(f"  Pociatocne skore: {initial_score:.1f}")
    print(f"  SA skore (5k it): {sa_score:.1f}")
    assert sa_score >= initial_score, "SA by nemalo zhorsiť pociatocne mapovanie!"
    print("  ✓ PASSED\n")


if __name__ == "__main__":
    test_caesar()
    test_incremental_scoring()
    test_sa_short()
    print("=== Vsetky testy PASSED ===")
