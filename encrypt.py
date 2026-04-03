"""
encrypt.py – Šifrovanie monoalfabetickou substitučnou šifrou.

Tento skript šifruje text rovnakým typom šifry, akou bol zašifrovaný
crypt.txt v tomto projekte: monoalfabetická substitúcia (každé písmeno
abecedy sa nahradí iným, vždy rovnakým písmenom).

Použitie:
    python3 encrypt.py                      # interaktívny mód
    python3 encrypt.py -i input.txt         # šifruje súbor, náhodný kľúč
    python3 encrypt.py -i input.txt -k KEY  # šifruje súbor daným kľúčom
    python3 encrypt.py -i input.txt -o out.txt  # výstup do súboru
    python3 encrypt.py --from-decrypt-map   # invertuje dešifrovacie mapovanie

Kľúč (KEY) je 26-znakový reťazec: permutácia abecedy, kde
  pozícia 0  = čím sa nahradí 'a',
  pozícia 1  = čím sa nahradí 'b',
  ...
  pozícia 25 = čím sa nahradí 'z'.

Príklad: kľúč "zyxwvutsrqponmlkjihgfedcba" je jednoduchá inverzia abecedy
         (a↔z, b↔y, c↔x, ...).
"""

import argparse
import random
import string
import sys
import os


ALPHABET = "abcdefghijklmnopqrstuvwxyz"


# ---------------------------------------------------------------------------
# Generovanie kľúča
# ---------------------------------------------------------------------------

def generate_random_key():
    """Vygeneruje náhodný substitučný kľúč (permutáciu abecedy)."""
    key = list(ALPHABET)
    random.shuffle(key)
    return "".join(key)


def key_to_mapping(key):
    """
    Konvertuje 26-znakový kľúč na slovník { plaintext_char: cipher_char }.
    Kľúč[i] hovorí, čím nahradiť i-te písmeno abecedy.
    """
    if len(key) != 26 or sorted(key.lower()) != list(ALPHABET):
        raise ValueError(
            f"Kľúč musí byť permutácia 26 písmen abecedy.\n"
            f"Dostali sme: '{key}' (dĺžka {len(key)})"
        )
    return {ALPHABET[i]: key[i].lower() for i in range(26)}


def invert_mapping(mapping):
    """
    Invertuje mapovanie: ak decrypt_map[cipher] = plain,
    vráti encrypt_map[plain] = cipher.
    """
    return {v: k for k, v in mapping.items()}


def mapping_to_key(mapping):
    """Konvertuje slovník mapovania na 26-znakový kľúč."""
    return "".join(mapping.get(c, c) for c in ALPHABET)


# ---------------------------------------------------------------------------
# Šifrovanie
# ---------------------------------------------------------------------------

def encrypt_text(text, mapping):
    """
    Zašifruje text pomocou substitučného mapovania.
    Zachováva veľkosť písmen a nealfabetické znaky.
    """
    result = []
    for char in text:
        key = char.lower()
        if key in mapping:
            enc = mapping[key]
            result.append(enc.upper() if char.isupper() else enc)
        else:
            result.append(char)
    return "".join(result)


def decrypt_text(text, mapping):
    """
    Dešifruje text (invertuje mapovanie a aplikuje).
    Pre overenie, že šifrovanie funguje správne.
    """
    inv = invert_mapping(mapping)
    return encrypt_text(text, inv)


# ---------------------------------------------------------------------------
# Vstup / Výstup
# ---------------------------------------------------------------------------

def parse_decrypt_mapping(map_str):
    """
    Parsuje mapovanie z formátu, aký používa decrypt_revised2.py.
    Akceptuje:
      - Python dict string: {'a': 'q', 'b': 'w', ...}
      - Čistý 26-znakový kľúč: qwertyuiopasdfghjklzxcvbnm
    """
    map_str = map_str.strip()

    # Skús ako 26-znakový kľúč
    if len(map_str) == 26 and map_str.isalpha():
        return key_to_mapping(map_str)

    # Skús ako Python dict
    import ast
    try:
        d = ast.literal_eval(map_str)
        if isinstance(d, dict):
            return d
    except (ValueError, SyntaxError):
        pass

    raise ValueError(f"Nepodarilo sa parsovať mapovanie: '{map_str[:50]}...'")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Šifrovanie monoalfabetickou substitučnou šifrou",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Príklady:
  %(prog)s -i vstup.txt                     Šifruje náhodným kľúčom
  %(prog)s -i vstup.txt -k qwert...         Šifruje daným kľúčom
  %(prog)s -i vstup.txt -o sifra.txt        Výstup do súboru
  %(prog)s --from-decrypt-map '{...}'       Invertuje dešifrovacie mapovanie
        """
    )
    parser.add_argument("-i", "--input", help="Vstupný súbor s textom na šifrovanie")
    parser.add_argument("-o", "--output", help="Výstupný súbor (predvolené: stdout)")
    parser.add_argument("-k", "--key", help="26-znakový substitučný kľúč (permutácia abecedy)")
    parser.add_argument("--from-decrypt-map",
                        help="Dešifrovacie mapovanie na invertovanie (dict alebo 26-znakový kľúč)")
    parser.add_argument("--verify", action="store_true",
                        help="Overí šifrovanie dešifrovaním a porovnaním s originálom")

    args = parser.parse_args()

    # ----- Zostavenie mapovania -----
    if args.from_decrypt_map:
        # Invertuj dešifrovacie mapovanie → šifrovacie mapovanie
        decrypt_map = parse_decrypt_mapping(args.from_decrypt_map)
        encrypt_map = invert_mapping(decrypt_map)
        key = mapping_to_key(encrypt_map)
        print(f"Invertované dešifrovacie mapovanie → šifrovací kľúč: {key}")
    elif args.key:
        key = args.key.lower()
        encrypt_map = key_to_mapping(key)
        print(f"Použitý kľúč: {key}")
    else:
        key = generate_random_key()
        encrypt_map = key_to_mapping(key)
        print(f"Vygenerovaný náhodný kľúč: {key}")

    # Zobraz mapovanie
    print("\nMapovanie (plaintext → šifrované):")
    for i in range(0, 26, 13):
        plain_row  = " ".join(ALPHABET[i:i+13])
        cipher_row = " ".join(encrypt_map[c] for c in ALPHABET[i:i+13])
        print(f"  {plain_row}")
        print(f"  {cipher_row}")
        print()

    # ----- Načítanie textu -----
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            plaintext = f.read()
        print(f"Načítaný vstupný súbor: {args.input} ({len(plaintext)} znakov)")
    else:
        print("\nZadajte text na šifrovanie (ukončite Ctrl+D alebo prázdnym riadkom):")
        lines = []
        try:
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
        except EOFError:
            pass
        plaintext = "\n".join(lines)
        if not plaintext.strip():
            print("Žiadny text na šifrovanie. Koniec.")
            sys.exit(0)

    # ----- Šifrovanie -----
    ciphertext = encrypt_text(plaintext, encrypt_map)

    # ----- Výstup -----
    print("\n" + "=" * 60)
    print("ZAŠIFROVANÝ TEXT:")
    print("=" * 60)
    print(ciphertext)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(ciphertext)
        print(f"\nZašifrovaný text uložený do: {args.output}")

    # Ulož kľúč vedľa výstupu
    key_info = f"""
---
Šifrovací kľúč
---------------
Kľúč:       {key}
Mapovanie:  {encrypt_map}
Inverzný:   {invert_mapping(encrypt_map)}
"""
    if args.output:
        key_path = args.output.rsplit('.', 1)
        key_file = f"{key_path[0]}_kluc.txt" if len(key_path) > 1 else f"{args.output}_kluc.txt"
        with open(key_file, 'w', encoding='utf-8') as f:
            f.write(key_info)
        print(f"Kľúč uložený do: {key_file}")

    # ----- Verifikácia -----
    if args.verify:
        print("\n" + "=" * 60)
        print("VERIFIKÁCIA (dešifrovanie šifrovaného textu):")
        print("=" * 60)
        decrypted = decrypt_text(ciphertext, encrypt_map)
        if decrypted == plaintext:
            print("✓ ÚSPECH: Dešifrovaný text sa zhoduje s originálom.")
        else:
            print("✗ CHYBA: Dešifrovaný text sa NEZHODUJE s originálom!")
            # Zobraz prvý rozdiel
            for i, (a, b) in enumerate(zip(plaintext, decrypted)):
                if a != b:
                    print(f"  Prvý rozdiel na pozícii {i}: '{a}' vs '{b}'")
                    break
        print(f"\nDešifrovaný text:\n{decrypted}")


if __name__ == "__main__":
    main()
