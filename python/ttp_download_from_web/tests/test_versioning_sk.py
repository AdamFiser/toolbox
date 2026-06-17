"""Testy rozpoznání verze tabulky ŽSR z textu odkazu."""

from __future__ import annotations

from ttp_sk.versioning import parse_sk_link, select_latest


class TestParseSkLink:
    def test_zaklad(self):
        t = parse_sk_link("TTP 101 A zmena č. 32")
        assert t is not None
        assert t.identity == "TTP 101 A"
        assert t.change == 32
        assert t.filename == "TTP 101 A.pdf"

    def test_vicemistne_cislo_zmeny(self):
        t = parse_sk_link("TTP 106 A zmena č. 83")
        assert t.identity == "TTP 106 A"
        assert t.change == 83

    def test_bez_pismene(self):
        t = parse_sk_link("TTP 130 zmena č. 5")
        assert t.identity == "TTP 130"
        assert t.change == 5

    def test_zbytecne_mezery(self):
        t = parse_sk_link("  TTP   101   A   zmena č.  32 ")
        assert t.identity == "TTP 101 A"
        assert t.change == 32

    def test_neshoda(self):
        assert parse_sk_link("Popis tabuliek podľa predpisu") is None
        assert parse_sk_link("") is None


class TestSelectLatest:
    def test_vybere_nejvyssi_zmenu(self):
        tabs = [
            parse_sk_link("TTP 106 D zmena č. 82"),
            parse_sk_link("TTP 106 D zmena č. 84"),
        ]
        latest = select_latest(tabs)
        assert len(latest) == 1
        assert latest[0].change == 84

    def test_ruzne_identity_zustanou(self):
        tabs = [
            parse_sk_link("TTP 101 A zmena č. 32"),
            parse_sk_link("TTP 101 B zmena č. 31"),
        ]
        latest = select_latest(tabs)
        assert len(latest) == 2

    def test_prazdny_seznam(self):
        assert select_latest([]) == []
