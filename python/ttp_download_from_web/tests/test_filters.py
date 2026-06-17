"""Testy pravidel pro vyřazení souborů a větví menu."""

from __future__ import annotations

from ttp_sz.filters import (
    is_body_trati_ttp_zip,
    is_excluded_menu_item,
    is_xml_suffix,
    should_skip,
)


class TestIsXmlSuffix:
    def test_xml_zip(self):
        assert is_xml_suffix("tabulka_xml.zip") is True

    def test_xml_bez_pripony(self):
        assert is_xml_suffix("tabulka_xml") is True

    def test_velikost_pismen(self):
        assert is_xml_suffix("tabulka_XML.zip") is True

    def test_neni_xml(self):
        assert is_xml_suffix("tabulka.zip") is False
        assert is_xml_suffix("xmlnice.pdf") is False

    def test_prazdny(self):
        assert is_xml_suffix("") is False


class TestIsBodyTratiTtpZip:
    def test_zaklad(self):
        assert is_body_trati_ttp_zip("Body tratí TTP.zip") is True

    def test_bez_diakritiky(self):
        assert is_body_trati_ttp_zip("Body trati TTP.zip") is True

    def test_s_prefixem(self):
        assert is_body_trati_ttp_zip("301 Body tratí TTP.zip") is True

    def test_neni_zip(self):
        assert is_body_trati_ttp_zip("Body tratí TTP.pdf") is False

    def test_jiny_nazev(self):
        assert is_body_trati_ttp_zip("Seznam tratí.zip") is False


class TestShouldSkip:
    def test_xml(self):
        assert should_skip("neco_xml.zip") is True

    def test_body_trati(self):
        assert should_skip("Body tratí TTP.zip") is True

    def test_bezny_soubor(self):
        assert should_skip("304C_01_20260415.pdf") is False


class TestIsExcludedMenuItem:
    def test_label_xml(self):
        assert is_excluded_menu_item("XML", []) is True

    def test_predek_xml(self):
        assert is_excluded_menu_item("Tabulky", ["TTP", "xml", "Tabulky"]) is True

    def test_bezna_polozka(self):
        assert is_excluded_menu_item("Tabulky 3XX", ["TTP", "Tabulky 3XX"]) is False

    def test_prazdne(self):
        assert is_excluded_menu_item(None, None) is False
