"""Testy rozpoznání verze souboru podle datového suffixu."""

from __future__ import annotations

from datetime import date

from ttp_sz.versioning import parse_version


class TestParseVersionDatum:
    def test_suffix_podtrzitkem(self):
        v = parse_version("304C_01_20260415.pdf")
        assert v.version_date == date(2026, 4, 15)

    def test_suffix_pomlckou(self):
        v = parse_version("301A_02-20251214.pdf")
        assert v.version_date == date(2025, 12, 14)

    def test_suffix_mezerou(self):
        v = parse_version("Seznam tratí TTP - změny 20251214.pdf")
        assert v.version_date == date(2025, 12, 14)

    def test_bez_data(self):
        v = parse_version("Vysvětlivky k TTP.pdf")
        assert v.version_date is None

    def test_teckovy_format_neni_rozpoznan(self):
        # DD.MM.YYYY není 8 číslic pohromadě → fallback na porovnání názvem.
        v = parse_version("Mapa tratí TTP 14.12.2025.pdf")
        assert v.version_date is None

    def test_nevalidni_datum_ignorovano(self):
        # 20221507 má měsíc 15 → nevalidní, není verzní datum.
        v = parse_version("Vysvětlivky k TTP_20221507.pdf")
        assert v.version_date is None

    def test_vybere_nejpravejsi_token(self):
        v = parse_version("zaloha_20200101_aktual_20260618.pdf")
        assert v.version_date == date(2026, 6, 18)


class TestParseVersionIdentita:
    def test_dve_verze_maji_stejnou_identitu(self):
        a = parse_version("304C_01_20260415.pdf")
        b = parse_version("304C_01_20260618.pdf")
        assert a.identity == b.identity

    def test_identita_bez_diakritiky_a_casefold(self):
        a = parse_version("Tabulky tratí_20260101.pdf")
        b = parse_version("TABULKY TRATI_20260202.pdf")
        assert a.identity == b.identity

    def test_ruzne_soubory_ruzna_identita(self):
        a = parse_version("304C_01_20260415.pdf")
        b = parse_version("304C_02_20260415.pdf")
        assert a.identity != b.identity

    def test_ruzna_pripona_ruzna_identita(self):
        a = parse_version("seznam_20260101.pdf")
        b = parse_version("seznam_20260101.zip")
        assert a.identity != b.identity

    def test_original_zachovan(self):
        v = parse_version("304C_01_20260415.pdf")
        assert v.original == "304C_01_20260415.pdf"

    def test_basename_z_cesty(self):
        v = parse_version("Tabulky 3XX/304/304C/304C_01_20260415.pdf")
        assert v.original == "304C_01_20260415.pdf"
        assert v.version_date == date(2026, 4, 15)
