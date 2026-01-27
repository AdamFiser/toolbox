#!/usr/bin/env python3
from __future__ import annotations

import re


def normalize_hex(s: str) -> str:
    """Remove separators and validate hex."""
    h = re.sub(r"[^0-9a-fA-F]", "", s).upper()
    if not h:
        raise ValueError("Prázdný vstup.")
    if len(h) % 2 != 0:
        raise ValueError(f"Hex musí mít sudý počet znaků (teď {len(h)}).")
    return h


def hex_to_bytes(h: str) -> list[int]:
    h = normalize_hex(h)
    return [int(h[i:i+2], 16) for i in range(0, len(h), 2)]


def bytes_to_hex(b: list[int]) -> str:
    return "".join(f"{x:02X}" for x in b)


def hex_uid_to_dec_reversed(uid_hex: str) -> int:
    """HEX UID -> reverse byte order -> DEC."""
    b = hex_to_bytes(uid_hex)
    rev_hex = bytes_to_hex(list(reversed(b)))
    return int(rev_hex, 16)


def minimal_bytes_for_dec(n: int) -> int:
    """Smallest whole-byte length to represent n."""
    if n < 0:
        raise ValueError("DEC číslo musí být nezáporné.")
    bits = n.bit_length()
    return max(1, (bits + 7) // 8)


def dec_to_hex_uid_reversed(dec_value: int, n_bytes: int | None = None) -> str:
    """
    DEC -> HEX (padded to n_bytes) -> reverse bytes back to 'normal' UID hex.
    If n_bytes is None, choose minimal bytes to represent the value.
    """
    if dec_value < 0:
        raise ValueError("DEC číslo musí být nezáporné.")
    if n_bytes is None:
        n_bytes = minimal_bytes_for_dec(dec_value)

    hex_width = n_bytes * 2
    h = f"{dec_value:0{hex_width}X}"
    b = [int(h[i:i+2], 16) for i in range(0, len(h), 2)]
    return bytes_to_hex(list(reversed(b)))


def is_decimal_input(s: str) -> bool:
    return bool(re.fullmatch(r"\d+", s.strip()))


def main() -> None:
    print("RFID převod (MIFARE Ultralight / UID): HEX <-> DEC (reverse bytes)")
    print("Zadej HEX (např. 043B4B898A0280 nebo '04 3B 4B 89 8A 02 80')")
    print("nebo DEC (např. 36031591051115268).")
    raw = input("Vstup: ").strip()

    if not raw:
        print("Prázdný vstup.")
        return

    try:
        if is_decimal_input(raw):
            dec_val = int(raw, 10)
            # auto-odhad délky v bytech; u Ultralight je často 7 bytů,
            # ale tady to necháme automaticky podle hodnoty
            uid_hex = dec_to_hex_uid_reversed(dec_val, n_bytes=None)
            print("\nDetekováno: DEC")
            print("Výstup HEX UID: ", uid_hex)
            print("Byty:          ", " ".join(uid_hex[i:i+2] for i in range(0, len(uid_hex), 2)))
            print("Použito bytů:  ", len(uid_hex) // 2)

        else:
            uid_hex_norm = normalize_hex(raw)
            dec_val = hex_uid_to_dec_reversed(uid_hex_norm)
            print("\nDetekováno: HEX")
            print("Normalizovaný HEX UID:", uid_hex_norm)
            print("Byty:                ", " ".join(uid_hex_norm[i:i+2] for i in range(0, len(uid_hex_norm), 2)))
            print("Výstup DEC:          ", dec_val)

    except ValueError as e:
        print(f"Chyba: {e}")


if __name__ == "__main__":
    main()
